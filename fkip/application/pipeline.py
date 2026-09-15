from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from fkip.application.metrics import PipelineError, PipelineRunResult, PipelineRunTracker
from fkip.domain.chunking import chunk_document_text
from fkip.domain.models import DocumentSource, FinancialDocument, ProcessedDocument, SourceType
from fkip.domain.processing import process_document
from fkip.domain.quality import canonical_source_key, validate_document, validate_source
from fkip.infrastructure.document_reader import read_document_text
from fkip.infrastructure.metadata_repository import MetadataRepository
from fkip.infrastructure.object_storage import ObjectStorage
from fkip.infrastructure.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        metadata_repository: MetadataRepository,
        object_storage: ObjectStorage,
        vector_store: VectorStore,
    ) -> None:
        self.metadata_repository = metadata_repository
        self.object_storage = object_storage
        self.vector_store = vector_store

    def ingest_manifest(self, manifest_path: Path) -> PipelineRunResult:
        tracker = PipelineRunTracker(run_id=f"manifest:{manifest_path}:{uuid4()}")
        with manifest_path.open("r", encoding="utf-8") as file:
            raw_sources = json.load(file)

        tracker.result.sources_seen = len(raw_sources)
        self.metadata_repository.record_ingestion_run(tracker.result, manifest_path=str(manifest_path))
        sources = [
            DocumentSource(
                uri=item["uri"],
                source_type=SourceType(item["source_type"]),
                title=item.get("title"),
                issuer=item.get("issuer"),
                published_at=item.get("published_at"),
            )
            for item in raw_sources
        ]

        seen_source_keys: set[str] = set()
        for source in sources:
            source_key = canonical_source_key(source)
            if source_key in seen_source_keys:
                tracker.result.duplicate_sources += 1
                tracker.result.documents_skipped += 1
                self.metadata_repository.record_ingestion_item(
                    run_id=tracker.result.run_id,
                    source_uri=source.uri,
                    status="skipped",
                    stage="duplicate_detection",
                    error_message="Duplicate source URI in manifest.",
                )
                logger.warning("duplicate_source_skipped", extra={"uri": source.uri})
                continue
            seen_source_keys.add(source_key)

            processed = self._safe_ingest_source(source, tracker.result)
            if processed is not None:
                tracker.result.documents_ingested += 1
                tracker.result.document_ids.append(processed.document_id)
                self.metadata_repository.record_ingestion_item(
                    run_id=tracker.result.run_id,
                    source_uri=source.uri,
                    status="ingested",
                    document_id=processed.document_id,
                    stage="completed",
                )

        result = tracker.finish()
        self.metadata_repository.record_ingestion_run(result, manifest_path=str(manifest_path))
        return result

    def _safe_ingest_source(self, source: DocumentSource, result: PipelineRunResult) -> ProcessedDocument | None:
        source_validation = validate_source(source)
        if not source_validation.valid:
            result.validation_failures += 1
            result.documents_skipped += 1
            for issue in source_validation.issues:
                result.errors.append(PipelineError(source.uri, "source_validation", f"{issue.field}: {issue.message}"))
            self.metadata_repository.record_ingestion_item(
                run_id=result.run_id,
                source_uri=source.uri,
                status="failed",
                stage="source_validation",
                error_message="; ".join(f"{issue.field}: {issue.message}" for issue in source_validation.issues),
            )
            logger.warning("source_validation_failed", extra={"uri": source.uri, "issues": [issue.message for issue in source_validation.issues]})
            return None

        try:
            return self.ingest_source(source)
        except Exception as exc:
            result.documents_skipped += 1
            result.errors.append(PipelineError(source.uri, "ingestion", str(exc)))
            self.metadata_repository.record_ingestion_item(
                run_id=result.run_id,
                source_uri=source.uri,
                status="failed",
                stage="ingestion",
                error_message=str(exc),
            )
            logger.exception("document_ingestion_failed", extra={"uri": source.uri})
            return None

    def ingest_source(self, source: DocumentSource) -> ProcessedDocument:
        logger.info("ingesting document", extra={"uri": source.uri, "source_type": source.source_type})
        raw_text = read_document_text(source.uri)
        document = FinancialDocument(
            document_id=str(uuid5(NAMESPACE_URL, source.uri)),
            title=source.title or Path(source.uri).stem,
            source_type=source.source_type,
            raw_text=raw_text,
            uri=source.uri,
            issuer=source.issuer,
            published_at=source.published_at,
        )
        document_validation = validate_document(document)
        if not document_validation.valid:
            issue_text = "; ".join(f"{issue.field}: {issue.message}" for issue in document_validation.issues)
            raise ValueError(f"Document validation failed: {issue_text}")
        object_key = self.object_storage.put_text(document.document_id, raw_text)
        processed = process_document(document, object_key)
        self.metadata_repository.upsert(processed)
        self.metadata_repository.record_document_source(processed)
        self.vector_store.upsert(processed)
        self.vector_store.upsert_chunks(processed, chunk_document_text(processed.document_id, processed.clean_text))
        logger.info("document ingested", extra={"document_id": processed.document_id, "title": processed.title})
        return processed
