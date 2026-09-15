import unittest
from datetime import UTC, datetime
from uuid import uuid4

from fkip.domain.models import SourceType
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository


class MetadataRepositoryTests(unittest.TestCase):
    def test_from_row_normalises_uuid_document_id_to_string(self):
        document_id = uuid4()
        row = (
            document_id,
            "Annual Report",
            "annual_report",
            "Example Bank",
            "2025-01-01",
            "source.html",
            "object.txt",
            "Revenue capital liquidity risk " * 5,
            "Summary",
            ["revenue", "capital"],
            ["Risk & Compliance"],
            datetime.now(UTC),
        )

        document = SQLiteMetadataRepository._from_row(row)

        self.assertEqual(document.document_id, str(document_id))
        self.assertIsInstance(document.document_id, str)
        self.assertEqual(document.source_type, SourceType.ANNUAL_REPORT)


if __name__ == "__main__":
    unittest.main()
