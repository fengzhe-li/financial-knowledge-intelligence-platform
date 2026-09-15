from __future__ import annotations

import json
import statistics
import tempfile
from pathlib import Path
from time import perf_counter

from fkip.application.pipeline import IngestionPipeline
from fkip.config import settings
from fkip.infrastructure.metadata_repository import SQLiteMetadataRepository
from fkip.infrastructure.object_storage import LocalObjectStorage
from fkip.infrastructure.vector_store import LocalVectorStore


def run_ingestion_benchmark(manifest_path: Path, iterations: int = 3) -> dict:
    durations: list[float] = []
    documents_per_run: list[int] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for iteration in range(iterations):
            pipeline = IngestionPipeline(
                metadata_repository=SQLiteMetadataRepository(root / f"metadata-{iteration}.db"),
                object_storage=LocalObjectStorage(root / f"documents-{iteration}"),
                vector_store=LocalVectorStore(root / f"index-{iteration}.json"),
            )
            started = perf_counter()
            result = pipeline.ingest_manifest(manifest_path)
            durations.append(perf_counter() - started)
            documents_per_run.append(result.documents_ingested)

    total_documents = sum(documents_per_run)
    mean_duration = statistics.mean(durations) if durations else 0.0
    throughput = total_documents / sum(durations) if sum(durations) > 0 else 0.0
    return {
        "manifest": str(manifest_path),
        "iterations": iterations,
        "environment": settings.environment,
        "documents_processed": total_documents,
        "mean_duration_seconds": round(mean_duration, 4),
        "min_duration_seconds": round(min(durations), 4) if durations else 0.0,
        "max_duration_seconds": round(max(durations), 4) if durations else 0.0,
        "throughput_docs_per_second": round(throughput, 4),
    }


def write_benchmark(result: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

