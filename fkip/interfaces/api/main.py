from __future__ import annotations

import json
import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from fkip.application.metrics import compute_overview_statistics
from fkip.bootstrap import build_analysis_service, build_metadata_repository, build_pipeline, build_vector_store
from fkip.config import settings
from fkip.domain.models import DocumentSource, SourceType

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    uri: str
    source_type: SourceType
    title: str | None = None
    issuer: str | None = None
    published_at: str | None = None


class AnalysisRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    limit: int = Field(5, ge=1, le=20)


class CompareRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    issuer_a: str = Field(..., min_length=2, max_length=100)
    issuer_b: str = Field(..., min_length=2, max_length=100)
    limit: int = Field(4, ge=1, le=10)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/overview")
def overview() -> dict:
    repo = build_metadata_repository()
    return compute_overview_statistics(repo, settings.pipeline_metrics_path)


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


@app.get("/pipeline-runs")
def list_pipeline_runs(limit: int = Query(10, ge=1, le=50)) -> list[dict]:
    repo = build_metadata_repository()
    return repo.list_ingestion_runs(limit=limit)


@app.post("/documents")
def ingest_document(request: IngestRequest) -> dict:
    pipeline = build_pipeline()
    processed = pipeline.ingest_source(DocumentSource(**request.model_dump()))
    return {"document_id": processed.document_id, "title": processed.title, "topics": processed.topics}


@app.get("/documents")
def list_documents(
    page: int | None = Query(None, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    q: str | None = Query(None, max_length=200),
    issuer: str | None = Query(None, max_length=100),
    source_type: str | None = Query(None, max_length=50),
    year: str | None = Query(None, max_length=10),
):
    all_documents = build_metadata_repository().list_documents()

    if page is None and q is None and issuer is None and source_type is None and year is None:
        return [
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type.value,
                "issuer": document.issuer,
                "published_at": document.published_at,
                "topics": document.topics,
            }
            for document in all_documents
        ]

    available_issuers = sorted({d.issuer for d in all_documents if d.issuer})
    available_source_types = sorted({d.source_type.value for d in all_documents})
    available_years = sorted({str(d.published_at)[:4] for d in all_documents if d.published_at})

    filtered = all_documents
    if q:
        query_lower = q.strip().lower()
        filtered = [
            d
            for d in filtered
            if query_lower in d.title.lower()
            or (d.issuer and query_lower in d.issuer.lower())
            or query_lower in d.summary.lower()
            or any(query_lower in kw.lower() for kw in d.keywords)
            or any(query_lower in tp.lower() for tp in d.topics)
        ]
    if issuer:
        clean_issuer = issuer.strip().lower()
        filtered = [d for d in filtered if d.issuer and d.issuer.strip().lower() == clean_issuer]
    if source_type:
        clean_st = source_type.strip().lower()
        filtered = [d for d in filtered if d.source_type.value.lower() == clean_st]
    if year:
        clean_year = year.strip()
        filtered = [d for d in filtered if d.published_at and str(d.published_at).startswith(clean_year)]

    total = len(filtered)
    current_page = page or 1
    total_pages = max(1, math.ceil(total / page_size))
    offset = (current_page - 1) * page_size
    page_items = filtered[offset : offset + page_size]

    return {
        "items": [
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_type": document.source_type.value,
                "issuer": document.issuer,
                "published_at": document.published_at,
                "topics": document.topics,
                "keywords": document.keywords,
                "summary": document.summary,
                "uri": document.uri,
            }
            for document in page_items
        ],
        "total": total,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "available_issuers": available_issuers,
        "available_source_types": available_source_types,
        "available_years": available_years,
    }


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
        "object_key": document.object_key,
        "clean_text": document.clean_text,
        "created_at": document.created_at.isoformat(),
    }


@app.get("/documents/{document_id}/chunks")
def get_document_chunks(document_id: str) -> list[dict]:
    chunks = build_vector_store().get_document_chunks(document_id)
    return chunks


@app.get("/search")
def search(q: str = Query(..., min_length=1, max_length=500), limit: int = Query(5, ge=1, le=50)) -> list[dict]:
    return build_vector_store().search(q, limit=limit)


@app.post("/analysis/answer")
def answer_question(request: AnalysisRequest) -> dict:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    result = build_analysis_service().answer_question(request.question, limit=request.limit)
    return result.to_dict()


@app.post("/analysis/compare")
def compare_companies(request: CompareRequest) -> dict:
    if not request.topic.strip() or not request.issuer_a.strip() or not request.issuer_b.strip():
        raise HTTPException(status_code=400, detail="Topic, issuer_a and issuer_b are all required")
    result = build_analysis_service().compare_issuers(
        topic=request.topic,
        issuer_a=request.issuer_a,
        issuer_b=request.issuer_b,
        limit=request.limit,
    )
    return result.to_dict()


frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/favicon.svg", include_in_schema=False)
    def serve_frontend_favicon():
        favicon_path = frontend_dist / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        return FileResponse(str(frontend_dist / "index.html"))


