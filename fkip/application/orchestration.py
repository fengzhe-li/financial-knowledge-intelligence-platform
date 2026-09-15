from __future__ import annotations

import logging
import time
from pathlib import Path

from fkip.application.metrics import PipelineRunResult, write_pipeline_metrics
from fkip.bootstrap import build_pipeline

logger = logging.getLogger(__name__)


def run_scheduled_ingestion(
    manifest_path: Path,
    metrics_path: Path,
    interval_seconds: int,
    max_runs: int | None = None,
) -> list[PipelineRunResult]:
    results: list[PipelineRunResult] = []
    runs_completed = 0
    while max_runs is None or runs_completed < max_runs:
        logger.info("scheduled_ingestion_run_started", extra={"manifest": str(manifest_path)})
        result = build_pipeline().ingest_manifest(manifest_path)
        write_pipeline_metrics(result, metrics_path)
        results.append(result)
        runs_completed += 1
        logger.info("scheduled_ingestion_run_finished", extra=result.to_dict())
        if max_runs is not None and runs_completed >= max_runs:
            break
        time.sleep(interval_seconds)
    return results

