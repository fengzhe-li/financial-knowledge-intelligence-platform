import unittest

from fkip.domain.chunking import chunk_document_text


class ChunkingTests(unittest.TestCase):
    def test_chunks_with_overlap_and_offsets(self):
        text = " ".join(f"word{i}" for i in range(20))

        chunks = chunk_document_text("doc-1", text, max_words=8, overlap_words=2)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].chunk_id, "doc-1:0")
        self.assertIn("word6", chunks[1].text)
        self.assertGreater(chunks[1].start_char, chunks[0].start_char)
        self.assertLessEqual(chunks[-1].end_char, len(text))


if __name__ == "__main__":
    unittest.main()
