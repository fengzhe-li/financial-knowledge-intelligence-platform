import os
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from fkip.domain.chunking import chunk_document_text
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.vector_store import QdrantVectorStore


@unittest.skipUnless(os.getenv("QDRANT_INTEGRATION_URL"), "Set QDRANT_INTEGRATION_URL to run Qdrant integration tests")
class QdrantVectorStoreIntegrationTests(unittest.TestCase):
    def test_qdrant_upsert_and_chunk_search(self):
        suffix = uuid4().hex
        store = QdrantVectorStore(
            base_url=os.environ["QDRANT_INTEGRATION_URL"],
            document_collection=f"fkip_test_documents_{suffix}",
            chunk_collection=f"fkip_test_chunks_{suffix}",
            dimensions=256,
        )
        document = ProcessedDocument(
            document_id=f"doc-{suffix}",
            title="FCA Resilience Filing",
            source_type=SourceType.FCA_REGULATORY,
            issuer="Financial Conduct Authority",
            published_at="2025-03-31",
            uri="source",
            object_key="doc.txt",
            clean_text="Operational resilience requires firms to define impact tolerances and maintain cyber resilience.",
            summary="Operational resilience guidance.",
            keywords=["operational", "resilience"],
            topics=["Risk & Compliance"],
            created_at=datetime.now(UTC),
        )

        store.upsert(document)
        store.upsert_chunks(document, chunk_document_text(document.document_id, document.clean_text, max_words=12, overlap_words=2))
        results = store.search_chunks("impact tolerances operational resilience", limit=1)

        self.assertEqual(results[0]["document_id"], document.document_id)
        self.assertIn("impact tolerances", results[0]["text"])


if __name__ == "__main__":
    unittest.main()
