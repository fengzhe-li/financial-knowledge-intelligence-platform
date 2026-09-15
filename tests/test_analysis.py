import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from fkip.application.analysis import FinancialAnalysisService
from fkip.domain.chunking import chunk_document_text
from fkip.domain.models import ProcessedDocument, SourceType
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository
from fkip.infrastructure.vector_store import LocalVectorStore


class AnalysisTests(unittest.TestCase):
    def test_answer_includes_citations_from_retrieved_chunks(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repository = SQLiteMetadataRepository(root / "metadata.db")
            vector_store = LocalVectorStore(root / "index.json")
            document = ProcessedDocument(
                document_id="doc-1",
                title="FCA Operational Resilience",
                source_type=SourceType.FCA_REGULATORY,
                issuer="Financial Conduct Authority",
                published_at="2025-03-31",
                uri="samples/fca.txt",
                object_key="doc-1.txt",
                clean_text=(
                    "The FCA expects firms to identify important business services and set impact tolerances. "
                    "Financial institutions should improve governance, third-party risk management and cyber resilience."
                ),
                summary="FCA operational resilience guidance.",
                keywords=["fca", "resilience"],
                topics=["Risk & Compliance"],
                created_at=datetime.now(UTC),
            )
            repository.upsert(document)
            vector_store.upsert(document)
            vector_store.upsert_chunks(document, chunk_document_text(document.document_id, document.clean_text, max_words=20, overlap_words=5))

            result = FinancialAnalysisService(vector_store, repository).answer_question("What does the FCA say about impact tolerances?", limit=2)

        self.assertEqual(result.retrieval_count, 2)
        self.assertIn("[1]", result.answer)
        self.assertEqual(result.citations[0].title, "FCA Operational Resilience")
        self.assertIn("impact tolerances", result.citations[0].excerpt)


if __name__ == "__main__":
    unittest.main()
