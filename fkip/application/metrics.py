from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter


@dataclass
class PipelineError:
    source_uri: str
    stage: str
    message: str


@dataclass
class PipelineRunResult:
    run_id: str
    started_at: str
    finished_at: str | None = None
    duration_seconds: float = 0.0
    sources_seen: int = 0
    documents_ingested: int = 0
    documents_skipped: int = 0
    duplicate_sources: int = 0
    validation_failures: int = 0
    errors: list[PipelineError] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PipelineRunTracker:
    def __init__(self, run_id: str) -> None:
        self._started_perf = perf_counter()
        self.result = PipelineRunResult(run_id=run_id, started_at=datetime.now(UTC).isoformat())

    def finish(self) -> PipelineRunResult:
        self.result.finished_at = datetime.now(UTC).isoformat()
        self.result.duration_seconds = round(perf_counter() - self._started_perf, 4)
        return self.result


def write_pipeline_metrics(result: PipelineRunResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")


def compute_overview_statistics(repository, metrics_path: Path | None = None) -> dict:
    from collections import Counter

    documents = repository.list_documents()
    total_docs = len(documents)
    issuers = sorted({d.issuer for d in documents if d.issuer})
    source_types = dict(Counter(d.source_type.value for d in documents).most_common())
    years = dict(sorted(Counter(str(d.published_at)[:4] for d in documents if d.published_at).items()))
    topics_counter: Counter[str] = Counter()
    for d in documents:
        for t in d.topics:
            topics_counter[t] += 1
    topics_dist = dict(topics_counter.most_common())

    recent_runs = repository.list_ingestion_runs(limit=5)

    latest_metrics = None
    if metrics_path and metrics_path.exists():
        try:
            latest_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "indexed_document_count": total_docs,
        "unique_issuers_count": len(issuers),
        "issuers": issuers,
        "source_type_distribution": source_types,
        "publication_year_distribution": years,
        "topic_distribution": topics_dist,
        "recent_documents": [
            {
                "document_id": d.document_id,
                "title": d.title,
                "issuer": d.issuer,
                "source_type": d.source_type.value,
                "published_at": d.published_at,
                "topics": d.topics,
            }
            for d in documents[:6]
        ],
        "recent_pipeline_runs": recent_runs,
        "latest_pipeline_metrics": latest_metrics,
    }

