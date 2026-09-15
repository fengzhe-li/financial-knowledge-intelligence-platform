import unittest

from fkip.domain.models import DocumentSource, FinancialDocument, SourceType
from fkip.domain.quality import validate_document, validate_source


class QualityTests(unittest.TestCase):
    def test_rejects_missing_local_source(self):
        result = validate_source(DocumentSource(uri="samples/missing.txt", source_type=SourceType.PUBLIC_REPORT))

        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].field, "uri")

    def test_rejects_short_extracted_document_text(self):
        result = validate_document(
            FinancialDocument(
                title="Short report",
                source_type=SourceType.PUBLIC_REPORT,
                raw_text="Too short.",
                uri="samples/report.txt",
            )
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].field, "raw_text")


if __name__ == "__main__":
    unittest.main()
