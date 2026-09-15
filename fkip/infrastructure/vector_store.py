from __future__ import annotations

import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from fkip.domain.chunking import DocumentChunk
from fkip.domain.models import ProcessedDocument
from fkip.infrastructure.embeddings import EmbeddingModel, HashingEmbeddingModel


class VectorStore:
    def upsert(self, document: ProcessedDocument) -> None:
        raise NotImplementedError

    def upsert_chunks(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> None:
        raise NotImplementedError

    def search(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError

    def search_chunks(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError


class LocalVectorStore(VectorStore):
    def __init__(self, index_path: Path, embedding_model: EmbeddingModel | None = None) -> None:
        self.index_path = index_path
        self.embedding_model = embedding_model or HashingEmbeddingModel()
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._write({"documents": [], "chunks": []})

    def upsert(self, document: ProcessedDocument) -> None:
        index = self._load()
        records = index["documents"]
        records = [record for record in records if record["document_id"] != document.document_id]
        records.append(
            {
                "document_id": document.document_id,
                "title": document.title,
                "summary": document.summary,
                "topics": document.topics,
                "vector": self.embedding_model.embed(document.clean_text),
            }
        )
        index["documents"] = records
        self._write(index)

    def upsert_chunks(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> None:
        index = self._load()
        records = [record for record in index["chunks"] if record["document_id"] != document.document_id]
        for chunk in chunks:
            records.append(
                {
                    "document_id": document.document_id,
                    "title": document.title,
                    "topics": document.topics,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "text": chunk.text,
                    "vector": self.embedding_model.embed(chunk.text),
                }
            )
        index["chunks"] = records
        self._write(index)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        query_vector = self.embedding_model.embed(query)
        scored = []
        for record in self._load()["documents"]:
            scored.append(
                {
                    "document_id": record["document_id"],
                    "title": record["title"],
                    "summary": record["summary"],
                    "topics": record["topics"],
                    "score": round(_cosine(query_vector, record["vector"]), 4),
                }
            )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]

    def search_chunks(self, query: str, limit: int = 5) -> list[dict]:
        query_vector = self.embedding_model.embed(query)
        scored = []
        for record in self._load()["chunks"]:
            scored.append(
                {
                    "document_id": record["document_id"],
                    "title": record["title"],
                    "topics": record["topics"],
                    "chunk_id": record["chunk_id"],
                    "chunk_index": record["chunk_index"],
                    "start_char": record["start_char"],
                    "end_char": record["end_char"],
                    "text": record["text"],
                    "score": round(_cosine(query_vector, record["vector"]), 4),
                }
            )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]

    def _load(self) -> dict[str, list[dict]]:
        if not self.index_path.exists() or self.index_path.stat().st_size == 0:
            return {"documents": [], "chunks": []}
        loaded = json.loads(self.index_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            return {"documents": loaded, "chunks": []}
        return {"documents": loaded.get("documents", []), "chunks": loaded.get("chunks", [])}

    def _write(self, index: dict[str, list[dict]]) -> None:
        temp_path = self.index_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        temp_path.replace(self.index_path)


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        base_url: str,
        document_collection: str,
        chunk_collection: str,
        embedding_model: EmbeddingModel | None = None,
        api_key: str | None = None,
        dimensions: int = 256,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.document_collection = document_collection
        self.chunk_collection = chunk_collection
        self.embedding_model = embedding_model or HashingEmbeddingModel(dimensions=dimensions)
        self.api_key = api_key
        self.dimensions = dimensions
        self._ensure_collection(self.document_collection)
        self._ensure_collection(self.chunk_collection)

    def upsert(self, document: ProcessedDocument) -> None:
        self._upsert_points(
            self.document_collection,
            [
                {
                    "id": _point_id(f"document:{document.document_id}"),
                    "vector": self.embedding_model.embed(document.clean_text),
                    "payload": {
                        "record_type": "document",
                        "document_id": document.document_id,
                        "title": document.title,
                        "summary": document.summary,
                        "topics": document.topics,
                    },
                }
            ],
        )

    def upsert_chunks(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> None:
        self._delete_by_document_id(self.chunk_collection, document.document_id)
        points = [
            {
                "id": _point_id(f"chunk:{chunk.chunk_id}"),
                "vector": self.embedding_model.embed(chunk.text),
                "payload": {
                    "record_type": "chunk",
                    "document_id": document.document_id,
                    "title": document.title,
                    "topics": document.topics,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "text": chunk.text,
                },
            }
            for chunk in chunks
        ]
        if points:
            self._upsert_points(self.chunk_collection, points)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        results = self._search(self.document_collection, query, limit)
        return [
            {
                "document_id": payload["document_id"],
                "title": payload["title"],
                "summary": payload["summary"],
                "topics": payload["topics"],
                "score": round(item.get("score", 0.0), 4),
            }
            for item in results
            for payload in [item.get("payload", {})]
        ]

    def search_chunks(self, query: str, limit: int = 5) -> list[dict]:
        results = self._search(self.chunk_collection, query, limit)
        return [
            {
                "document_id": payload["document_id"],
                "title": payload["title"],
                "topics": payload["topics"],
                "chunk_id": payload["chunk_id"],
                "chunk_index": payload["chunk_index"],
                "start_char": payload["start_char"],
                "end_char": payload["end_char"],
                "text": payload["text"],
                "score": round(item.get("score", 0.0), 4),
            }
            for item in results
            for payload in [item.get("payload", {})]
        ]

    def _ensure_collection(self, collection: str) -> None:
        self._request(
            "PUT",
            f"/collections/{collection}",
            {
                "vectors": {
                    "size": self.dimensions,
                    "distance": "Cosine",
                }
            },
        )

    def _upsert_points(self, collection: str, points: list[dict]) -> None:
        self._request("PUT", f"/collections/{collection}/points?wait=true", {"points": points})

    def _delete_by_document_id(self, collection: str, document_id: str) -> None:
        self._request(
            "POST",
            f"/collections/{collection}/points/delete?wait=true",
            {
                "filter": {
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": document_id},
                        }
                    ]
                }
            },
        )

    def _search(self, collection: str, query: str, limit: int) -> list[dict]:
        response = self._request(
            "POST",
            f"/collections/{collection}/points/search",
            {
                "vector": self.embedding_model.embed(query),
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
            },
        )
        return response.get("result", [])

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            if method == "PUT" and path.startswith("/collections/") and exc.code in {409}:
                return {"status": "ok", "result": "collection already exists"}
            raise RuntimeError(f"Qdrant request failed with HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not connect to Qdrant at {self.base_url}: {exc}") from exc


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _point_id(value: str) -> str:
    return str(uuid5(NAMESPACE_URL, value))
