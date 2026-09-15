import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from fkip.application.indexing import rebuild_vector_index
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository
from fkip.infrastructure.vector_store import LocalVectorStore


class IndexingTests(unittest.TestCase):
    def test_rebuild_vector_index_creates_chunk_records(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repository = SQLiteMetadataRepository(root / "metadata.db")
            vector_store = LocalVectorStore(root / "index.json")
            repository.upsert(
                ProcessedDocument(
                    document_id="doc-1",
                    title="Annual Report",
                    source_type=SourceType.ANNUAL_REPORT,
                    issuer="Example Bank",
                    published_at="2025-01-01",
                    uri="source",
                    object_key="doc-1.txt",
                    clean_text="Revenue capital liquidity risk " * 80,
                    summary="Summary.",
                    keywords=["revenue"],
                    topics=["Risk & Compliance"],
                    created_at=datetime.now(UTC),
                )
            )

            result = rebuild_vector_index(repository, vector_store)

        self.assertEqual(result.documents_indexed, 1)
        self.assertGreater(result.chunks_indexed, 0)


if __name__ == "__main__":
    unittest.main()
