from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from fkip.application.metrics import PipelineRunResult
from fkip.domain.models import ProcessedDocument, SourceType


class MetadataRepository:
    def upsert(self, document: ProcessedDocument) -> None:
        raise NotImplementedError

    def list_documents(self) -> list[ProcessedDocument]:
        raise NotImplementedError

    def get(self, document_id: str) -> ProcessedDocument | None:
        raise NotImplementedError

    def record_document_source(self, document: ProcessedDocument, metadata: dict | None = None) -> None:
        raise NotImplementedError

    def record_ingestion_run(self, result: PipelineRunResult, manifest_path: str | None = None) -> None:
        raise NotImplementedError

    def record_ingestion_item(
        self,
        run_id: str,
        source_uri: str,
        status: str,
        document_id: str | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError


class SQLiteMetadataRepository(MetadataRepository):
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    issuer TEXT,
                    published_at TEXT,
                    uri TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    clean_text TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    keywords_json TEXT NOT NULL,
                    topics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def upsert(self, document: ProcessedDocument) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO documents
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.document_id,
                    document.title,
                    document.source_type.value,
                    document.issuer,
                    document.published_at,
                    document.uri,
                    document.object_key,
                    document.clean_text,
                    document.summary,
                    json.dumps(document.keywords),
                    json.dumps(document.topics),
                    document.created_at.isoformat(),
                ),
            )

    def list_documents(self) -> list[ProcessedDocument]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, document_id: str) -> ProcessedDocument | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        return self._from_row(row) if row else None

    def record_document_source(self, document: ProcessedDocument, metadata: dict | None = None) -> None:
        return None

    def record_ingestion_run(self, result: PipelineRunResult, manifest_path: str | None = None) -> None:
        return None

    def record_ingestion_item(
        self,
        run_id: str,
        source_uri: str,
        status: str,
        document_id: str | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        return None

    @staticmethod
    def _from_row(row: tuple) -> ProcessedDocument:
        from datetime import date, datetime

        def _json_value(value):
            if isinstance(value, str):
                return json.loads(value)
            return value

        def _date_value(value):
            if isinstance(value, date) and not isinstance(value, datetime):
                return value.isoformat()
            return value

        return ProcessedDocument(
            document_id=str(row[0]),
            title=row[1],
            source_type=SourceType(row[2]),
            issuer=row[3],
            published_at=_date_value(row[4]),
            uri=row[5],
            object_key=row[6],
            clean_text=row[7],
            summary=row[8],
            keywords=_json_value(row[9]),
            topics=_json_value(row[10]),
            created_at=datetime.fromisoformat(row[11]) if isinstance(row[11], str) else row[11],
        )


class PostgresMetadataRepository(MetadataRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] to use PostgreSQL metadata storage.") from exc

        return psycopg.connect(self.database_url)

    def upsert(self, document: ProcessedDocument) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        document_id, title, source_type, issuer, published_at, uri,
                        object_key, clean_text, summary, keywords, topics, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, now())
                    ON CONFLICT (document_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source_type = EXCLUDED.source_type,
                        issuer = EXCLUDED.issuer,
                        published_at = EXCLUDED.published_at,
                        uri = EXCLUDED.uri,
                        object_key = EXCLUDED.object_key,
                        clean_text = EXCLUDED.clean_text,
                        summary = EXCLUDED.summary,
                        keywords = EXCLUDED.keywords,
                        topics = EXCLUDED.topics,
                        updated_at = now()
                    """,
                    (
                        document.document_id,
                        document.title,
                        document.source_type.value,
                        document.issuer,
                        document.published_at,
                        document.uri,
                        document.object_key,
                        document.clean_text,
                        document.summary,
                        json.dumps(document.keywords),
                        json.dumps(document.topics),
                        document.created_at.isoformat(),
                    ),
                )

    def list_documents(self) -> list[ProcessedDocument]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT document_id, title, source_type, issuer, published_at, uri, object_key,
                           clean_text, summary, keywords, topics, created_at
                    FROM documents
                    ORDER BY created_at DESC
                    """
                )
                rows = cursor.fetchall()
        return [SQLiteMetadataRepository._from_row(tuple(row)) for row in rows]

    def get(self, document_id: str) -> ProcessedDocument | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT document_id, title, source_type, issuer, published_at, uri, object_key,
                           clean_text, summary, keywords, topics, created_at
                    FROM documents
                    WHERE document_id = %s
                    """,
                    (document_id,),
                )
                row = cursor.fetchone()
        return SQLiteMetadataRepository._from_row(tuple(row)) if row else None

    def record_document_source(self, document: ProcessedDocument, metadata: dict | None = None) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO document_sources (
                        document_id, uri, source_type, issuer, published_at, title, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (document_id, uri) DO UPDATE SET
                        source_type = EXCLUDED.source_type,
                        issuer = EXCLUDED.issuer,
                        published_at = EXCLUDED.published_at,
                        title = EXCLUDED.title,
                        metadata = EXCLUDED.metadata
                    """,
                    (
                        document.document_id,
                        document.uri,
                        document.source_type.value,
                        document.issuer,
                        document.published_at,
                        document.title,
                        json.dumps(metadata or {}),
                    ),
                )

    def record_ingestion_run(self, result: PipelineRunResult, manifest_path: str | None = None) -> None:
        if result.finished_at is None:
            status = "running"
        else:
            status = "completed" if not result.errors else "completed_with_errors"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ingestion_runs (
                        run_id, status, manifest_path, started_at, finished_at, duration_seconds,
                        sources_seen, documents_ingested, documents_skipped, duplicate_sources,
                        validation_failures, error_count, metadata, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (run_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        manifest_path = EXCLUDED.manifest_path,
                        finished_at = EXCLUDED.finished_at,
                        duration_seconds = EXCLUDED.duration_seconds,
                        sources_seen = EXCLUDED.sources_seen,
                        documents_ingested = EXCLUDED.documents_ingested,
                        documents_skipped = EXCLUDED.documents_skipped,
                        duplicate_sources = EXCLUDED.duplicate_sources,
                        validation_failures = EXCLUDED.validation_failures,
                        error_count = EXCLUDED.error_count,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    (
                        result.run_id,
                        status,
                        manifest_path,
                        result.started_at,
                        result.finished_at,
                        result.duration_seconds,
                        result.sources_seen,
                        result.documents_ingested,
                        result.documents_skipped,
                        result.duplicate_sources,
                        result.validation_failures,
                        len(result.errors),
                        json.dumps({"document_ids": result.document_ids, "errors": [asdict(error) for error in result.errors]}),
                    ),
                )

    def record_ingestion_item(
        self,
        run_id: str,
        source_uri: str,
        status: str,
        document_id: str | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ingestion_items (
                        run_id, document_id, source_uri, status, stage, error_message, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (run_id, document_id, source_uri, status, stage, error_message, json.dumps(metadata or {})),
                )


def sqlite_path_from_url(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Expected sqlite database URL")
    return Path(database_url.replace("sqlite:///", ""))
