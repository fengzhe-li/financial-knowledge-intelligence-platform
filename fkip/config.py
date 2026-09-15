from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Financial Knowledge Intelligence Platform"
    environment: str = os.getenv("ENVIRONMENT", "local")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/metadata.db")
    object_store_path: Path = Path(os.getenv("OBJECT_STORE_PATH", "data/documents"))
    vector_index_path: Path = Path(os.getenv("VECTOR_INDEX_PATH", "data/index/vector_index.json"))
    vector_store_backend: str = os.getenv("VECTOR_STORE_BACKEND", "local")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_document_collection: str = os.getenv("QDRANT_DOCUMENT_COLLECTION", "fkip_documents")
    qdrant_chunk_collection: str = os.getenv("QDRANT_CHUNK_COLLECTION", "fkip_document_chunks")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "256"))
    pipeline_metrics_path: Path = Path(os.getenv("PIPELINE_METRICS_PATH", "data/metrics/latest_ingestion.json"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "extractive")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
