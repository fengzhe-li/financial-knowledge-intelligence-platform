from __future__ import annotations

from pathlib import Path

from fkip.application.analysis import ExtractiveFinancialSummariser, FinancialAnalysisService, OpenAiFinancialSummariser
from fkip.application.pipeline import IngestionPipeline
from fkip.config import settings
from fkip.infrastructure.metadata_repository import MetadataRepository, PostgresMetadataRepository, SQLiteMetadataRepository, sqlite_path_from_url
from fkip.infrastructure.embeddings import HashingEmbeddingModel
from fkip.infrastructure.object_storage import LocalObjectStorage
from fkip.infrastructure.vector_store import LocalVectorStore, QdrantVectorStore, VectorStore


def build_metadata_repository() -> MetadataRepository:
    if settings.database_url.startswith("postgres"):
        return PostgresMetadataRepository(settings.database_url)
    return SQLiteMetadataRepository(sqlite_path_from_url(settings.database_url))


def build_pipeline() -> IngestionPipeline:
    return IngestionPipeline(
        metadata_repository=build_metadata_repository(),
        object_storage=LocalObjectStorage(settings.object_store_path),
        vector_store=build_vector_store(),
    )


def build_analysis_service() -> FinancialAnalysisService:
    summariser = ExtractiveFinancialSummariser()
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY must be set when LLM_PROVIDER=openai")
        summariser = OpenAiFinancialSummariser(api_key=settings.openai_api_key, model=settings.openai_model)
    return FinancialAnalysisService(
        vector_store=build_vector_store(),
        metadata_repository=build_metadata_repository(),
        summariser=summariser,
    )


def build_vector_store() -> VectorStore:
    embedding_model = HashingEmbeddingModel(dimensions=settings.embedding_dimensions)
    if settings.vector_store_backend == "qdrant":
        return QdrantVectorStore(
            base_url=settings.qdrant_url,
            document_collection=settings.qdrant_document_collection,
            chunk_collection=settings.qdrant_chunk_collection,
            embedding_model=embedding_model,
            api_key=settings.qdrant_api_key,
            dimensions=settings.embedding_dimensions,
        )
    return LocalVectorStore(settings.vector_index_path, embedding_model=embedding_model)
