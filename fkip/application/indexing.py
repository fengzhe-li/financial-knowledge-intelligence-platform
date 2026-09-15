from __future__ import annotations

from dataclasses import dataclass

from fkip.domain.chunking import chunk_document_text
from fkip.infrastructure.metadata_repository import MetadataRepository
from fkip.infrastructure.vector_store import VectorStore


@dataclass(frozen=True)
class ReindexResult:
    documents_indexed: int
    chunks_indexed: int

    def to_dict(self) -> dict:
        return {"documents_indexed": self.documents_indexed, "chunks_indexed": self.chunks_indexed}


def rebuild_vector_index(metadata_repository: MetadataRepository, vector_store: VectorStore) -> ReindexResult:
    documents = metadata_repository.list_documents()
    chunks_indexed = 0
    for document in documents:
        chunks = chunk_document_text(document.document_id, document.clean_text)
        vector_store.upsert(document)
        vector_store.upsert_chunks(document, chunks)
        chunks_indexed += len(chunks)
    return ReindexResult(documents_indexed=len(documents), chunks_indexed=chunks_indexed)
