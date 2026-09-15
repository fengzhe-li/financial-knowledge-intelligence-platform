from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task


@dag(
    dag_id="financial_knowledge_ingestion",
    description="Scheduled ingestion workflow for financial document intelligence.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["fintech", "data-engineering", "retrieval"],
)
def financial_knowledge_ingestion():
    @task
    def ingest_manifest() -> dict:
        from fkip.bootstrap import build_pipeline

        result = build_pipeline().ingest_manifest(Path("samples/financial_sources.json"))
        return result.to_dict()

    @task
    def persist_metrics(result: dict) -> None:
        import json

        output = Path("data/metrics/latest_airflow_run.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    persist_metrics(ingest_manifest())


financial_knowledge_ingestion()
