from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fkip.bootstrap import build_analysis_service, build_metadata_repository, build_pipeline, build_vector_store
from fkip.config import settings
from fkip.domain.models import DocumentSource, SourceType

app = FastAPI(title=settings.app_name)


class IngestRequest(BaseModel):
    uri: str
    source_type: SourceType
    title: str | None = None
    issuer: str | None = None
    published_at: str | None = None


class AnalysisRequest(BaseModel):
    question: str
    limit: int = 5


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/pipeline-stats")
def pipeline_stats() -> dict:
    metrics_path = Path(settings.pipeline_metrics_path)
    if not metrics_path.exists():
        return {
            "available": False,
            "metrics_path": str(metrics_path),
            "message": "No pipeline metrics file found. Run ingestion with --metrics-output or set PIPELINE_METRICS_PATH.",
        }
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline metrics file is not valid JSON: {exc}") from exc
    return {"available": True, "metrics_path": str(metrics_path), "metrics": payload}


@app.post("/documents")
def ingest_document(request: IngestRequest) -> dict:
    pipeline = build_pipeline()
    processed = pipeline.ingest_source(DocumentSource(**request.model_dump()))
    return {"document_id": processed.document_id, "title": processed.title, "topics": processed.topics}


@app.get("/documents")
def list_documents() -> list[dict]:
    return [
        {
            "document_id": document.document_id,
            "title": document.title,
            "source_type": document.source_type.value,
            "issuer": document.issuer,
            "published_at": document.published_at,
            "topics": document.topics,
        }
        for document in build_metadata_repository().list_documents()
    ]


@app.get("/documents/{document_id}")
def get_document(document_id: str) -> dict:
    document = build_metadata_repository().get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "document_id": document.document_id,
        "title": document.title,
        "source_type": document.source_type.value,
        "issuer": document.issuer,
        "published_at": document.published_at,
        "summary": document.summary,
        "keywords": document.keywords,
        "topics": document.topics,
        "uri": document.uri,
    }


@app.get("/search")
def search(q: str, limit: int = 5) -> list[dict]:
    return build_vector_store().search(q, limit=limit)


@app.post("/analysis/answer")
def answer_question(request: AnalysisRequest) -> dict:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    result = build_analysis_service().answer_question(request.question, limit=request.limit)
    return result.to_dict()
