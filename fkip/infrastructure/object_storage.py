from __future__ import annotations

from pathlib import Path


class ObjectStorage:
    def put_text(self, document_id: str, raw_text: str) -> str:
        raise NotImplementedError

    def get_text(self, object_key: str) -> str:
        raise NotImplementedError


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put_text(self, document_id: str, raw_text: str) -> str:
        object_key = f"{document_id}.txt"
        path = self.root / object_key
        path.write_text(raw_text, encoding="utf-8")
        return object_key

    def get_text(self, object_key: str) -> str:
        return (self.root / object_key).read_text(encoding="utf-8")

