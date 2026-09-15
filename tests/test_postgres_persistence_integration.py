import os
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from fkip.application.metrics import PipelineRunResult
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.metadata_repository import PostgresMetadataRepository


@unittest.skipUnless(os.getenv("POSTGRES_INTEGRATION_DATABASE_URL"), "Set POSTGRES_INTEGRATION_DATABASE_URL to run PostgreSQL integration tests")
class PostgresPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.database_url = os.environ["POSTGRES_INTEGRATION_DATABASE_URL"]
        previous_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = self.database_url
        try:
            from alembic import command
            from alembic.config import Config

            command.upgrade(Config("alembic.ini"), "head")
        finally:
            if previous_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous_database_url

    def test_schema_and_repository_persistence(self):
        repository = PostgresMetadataRepository(self.database_url)
        suffix = uuid4().hex
        document_id = str(uuid4())
        run_id = f"integration-run-{suffix}"
        document = ProcessedDocument(
            document_id=document_id,
            title="Integration Annual Report",
            source_type=SourceType.ANNUAL_REPORT,
            issuer="Example Bank",
            published_at="2025-01-01",
            uri=f"source-{suffix}.html",
            object_key=f"{document_id}.txt",
            clean_text="Revenue capital liquidity risk " * 20,
            summary="Integration summary.",
            keywords=["revenue", "capital"],
            topics=["Risk & Compliance"],
            created_at=datetime.now(UTC),
        )

        repository.upsert(document)
        repository.record_document_source(document, metadata={"fixture": True})
        repository.record_ingestion_run(
            PipelineRunResult(
                run_id=run_id,
                started_at=datetime.now(UTC).isoformat(),
                finished_at=datetime.now(UTC).isoformat(),
                duration_seconds=0.1,
                sources_seen=1,
                documents_ingested=1,
                document_ids=[document_id],
            ),
            manifest_path="integration-manifest.json",
        )
        repository.record_ingestion_item(run_id=run_id, source_uri=document.uri, status="ingested", document_id=document_id, stage="completed")

        fetched = repository.get(document_id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Integration Annual Report")
        self.assertEqual(fetched.keywords, ["revenue", "capital"])
        self.assertTrue(_table_exists(repository, "document_sources"))
        self.assertTrue(_table_exists(repository, "ingestion_runs"))
        self.assertTrue(_table_exists(repository, "ingestion_items"))


def _table_exists(repository: PostgresMetadataRepository, table_name: str) -> bool:
    with repository._connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
                """,
                (table_name,),
            )
            return bool(cursor.fetchone()[0])


if __name__ == "__main__":
    unittest.main()
