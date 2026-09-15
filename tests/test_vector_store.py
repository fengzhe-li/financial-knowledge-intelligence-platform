import unittest
from datetime import UTC, datetime

from fkip.domain.chunking import chunk_document_text
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.vector_store import LocalVectorStore


class VectorStoreTests(unittest.TestCase):
    def test_vector_store_returns_relevant_results(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as temp_dir:
            store = LocalVectorStore(Path(temp_dir) / "index.json")
            store.upsert(
                document := ProcessedDocument(
                    document_id="doc-1",
                    title="Liquidity Risk",
                    source_type=SourceType.FCA_REGULATORY,
                    issuer="FCA",
                    published_at="2025-01-01",
                    uri="source",
                    object_key="doc-1.txt",
                    clean_text="liquidity capital risk compliance",
                    summary="Risk guidance.",
                    keywords=["liquidity", "risk"],
                    topics=["Risk & Compliance"],
                    created_at=datetime.now(UTC),
                )
            )
            store.upsert_chunks(document, chunk_document_text(document.document_id, document.clean_text, max_words=4, overlap_words=1))

            results = store.search("capital liquidity", limit=1)
            chunk_results = store.search_chunks("capital liquidity", limit=1)

        self.assertEqual(results[0]["document_id"], "doc-1")
        self.assertGreater(results[0]["score"], 0)
        self.assertEqual(chunk_results[0]["document_id"], "doc-1")
        self.assertIn("liquidity", chunk_results[0]["text"])


if __name__ == "__main__":
    unittest.main()
