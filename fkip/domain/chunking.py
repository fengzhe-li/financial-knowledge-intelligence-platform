from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    document_id: str
    chunk_id: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int


def chunk_document_text(document_id: str, text: str, max_words: int = 220, overlap_words: int = 40) -> list[DocumentChunk]:
    if max_words <= 0:
        raise ValueError("max_words must be greater than zero")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be non-negative and smaller than max_words")

    tokens = list(re.finditer(r"\S+", text))
    if not tokens:
        return []

    chunks: list[DocumentChunk] = []
    step = max_words - overlap_words
    for chunk_index, start_token in enumerate(range(0, len(tokens), step)):
        end_token = min(start_token + max_words, len(tokens))
        start_char = tokens[start_token].start()
        end_char = tokens[end_token - 1].end()
        chunk_text = text[start_char:end_char].strip()
        chunks.append(
            DocumentChunk(
                document_id=document_id,
                chunk_id=f"{document_id}:{chunk_index}",
                chunk_index=chunk_index,
                text=chunk_text,
                start_char=start_char,
                end_char=end_char,
            )
        )
        if end_token >= len(tokens):
            break
    return chunks

