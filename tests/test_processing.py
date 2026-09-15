import unittest

from fkip.domain.models import FinancialDocument, SourceType
from fkip.domain.processing import classify_topics, extract_keywords, process_document


class ProcessingTests(unittest.TestCase):
    def test_classifies_financial_risk_content(self):
        text = "The FCA expects firms to manage liquidity risk, capital controls and operational resilience."

        self.assertEqual(classify_topics(text)[0], "Risk & Compliance")

    def test_extract_keywords_filters_common_words(self):
        keywords = extract_keywords("The bank reported revenue revenue and capital discipline.")

        self.assertIn("revenue", keywords)
        self.assertNotIn("the", keywords)

    def test_process_document_preserves_metadata(self):
        document = FinancialDocument(
            title="Annual Report",
            source_type=SourceType.ANNUAL_REPORT,
            raw_text="Revenue increased. Capital remained resilient.",
            uri="local.txt",
            issuer="Example Bank",
            published_at="2025-01-01",
        )

        processed = process_document(document, "abc.txt")

        self.assertEqual(processed.title, "Annual Report")
        self.assertEqual(processed.issuer, "Example Bank")
        self.assertEqual(processed.object_key, "abc.txt")
        self.assertTrue(processed.summary.startswith("Revenue increased."))


if __name__ == "__main__":
    unittest.main()
