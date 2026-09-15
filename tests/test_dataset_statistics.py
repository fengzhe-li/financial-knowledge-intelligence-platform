import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.generate_dataset_statistics import generate_statistics


class DatasetStatisticsTests(unittest.TestCase):
    def test_generates_counts_from_manifest_and_metadata(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = root / "manifest.json"
            metadata = root / "metadata.jsonl"
            manifest.write_text(
                json.dumps(
                    [
                        {
                            "uri": "data/raw/sec/AAPL/10-K/a.html",
                            "source_type": "annual_report",
                            "issuer": "Apple Inc.",
                            "published_at": "2025-11-01",
                        },
                        {
                            "uri": "data/raw/sec/AAPL/10-Q/q.html",
                            "source_type": "public_report",
                            "issuer": "Apple Inc.",
                            "published_at": "2025-08-01",
                        },
                    ]
                ),
                encoding="utf-8",
            )
            metadata.write_text(
                "\n".join(
                    [
                        json.dumps({"local_path": "data/raw/sec/AAPL/10-K/a.html", "form_type": "10-K", "ticker": "AAPL", "file_size_bytes": 100}),
                        json.dumps({"local_path": "data/raw/sec/AAPL/10-Q/q.html", "form_type": "10-Q", "ticker": "AAPL", "file_size_bytes": 50}),
                    ]
                ),
                encoding="utf-8",
            )

            stats = generate_statistics(manifest, metadata)

        self.assertEqual(stats["total_documents"], 2)
        self.assertEqual(stats["source_types"]["annual_report"], 1)
        self.assertEqual(stats["form_types"]["10-Q"], 1)
        self.assertEqual(stats["downloaded_file_size_bytes"]["total"], 150)


if __name__ == "__main__":
    unittest.main()
