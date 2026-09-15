import json
import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fkip.application.pipeline import IngestionPipeline
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository
from fkip.infrastructure.object_storage import LocalObjectStorage
from fkip.infrastructure.vector_store import LocalVectorStore


class PipelineTests(unittest.TestCase):
    def test_manifest_ingestion_reports_duplicates_and_stats(self):
        pipeline_logger = logging.getLogger("fkip.application.pipeline")
        pipeline_logger.disabled = True
        try:
            with TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source_path = root / "report.txt"
                source_path.write_text(
                    "The FCA report discusses liquidity risk, capital planning, operational resilience and cyber controls.",
                    encoding="utf-8",
                )
                manifest_path = root / "manifest.json"
                manifest_path.write_text(
                    json.dumps(
                        [
                            {"uri": str(source_path), "source_type": "fca_regulatory", "title": "FCA Report"},
                            {"uri": str(source_path), "source_type": "fca_regulatory", "title": "Duplicate FCA Report"},
                        ]
                    ),
                    encoding="utf-8",
                )
                pipeline = IngestionPipeline(
                    metadata_repository=SQLiteMetadataRepository(root / "metadata.db"),
                    object_storage=LocalObjectStorage(root / "documents"),
                    vector_store=LocalVectorStore(root / "index.json"),
                )

                result = pipeline.ingest_manifest(manifest_path)
        finally:
            pipeline_logger.disabled = False

        self.assertEqual(result.sources_seen, 2)
        self.assertEqual(result.documents_ingested, 1)
        self.assertEqual(result.duplicate_sources, 1)
        self.assertEqual(result.documents_skipped, 1)


if __name__ == "__main__":
    unittest.main()
