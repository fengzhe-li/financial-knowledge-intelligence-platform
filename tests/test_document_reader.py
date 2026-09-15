import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fkip.infrastructure.document_reader import read_document_text


class DocumentReaderTests(unittest.TestCase):
    def test_strips_html_script_and_style_content(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "filing.html"
            path.write_text(
                "<html><style>.x{}</style><script>ignore()</script><body><h1>Annual Report</h1><p>Liquidity risk disclosure.</p></body></html>",
                encoding="utf-8",
            )

            text = read_document_text(str(path))

        self.assertIn("Annual Report", text)
        self.assertIn("Liquidity risk disclosure.", text)
        self.assertNotIn("ignore", text)


if __name__ == "__main__":
    unittest.main()
