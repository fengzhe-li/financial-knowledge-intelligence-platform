from __future__ import annotations

import argparse
import json
from pathlib import Path

from fkip.application.benchmarking import run_ingestion_benchmark, write_benchmark
from fkip.application.indexing import rebuild_vector_index
from fkip.application.metrics import write_pipeline_metrics
from fkip.application.orchestration import run_scheduled_ingestion
from fkip.application.reporting import write_report
from fkip.bootstrap import build_analysis_service, build_metadata_repository, build_pipeline, build_vector_store
from fkip.config import settings
from fkip.logging import configure_logging


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description=settings.app_name)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a JSON manifest of financial documents")
    ingest_parser.add_argument("manifest", type=Path)
    ingest_parser.add_argument("--metrics-output", type=Path, default=Path("data/metrics/latest_ingestion.json"))

    schedule_parser = subparsers.add_parser("schedule", help="Run scheduled manifest ingestion")
    schedule_parser.add_argument("manifest", type=Path)
    schedule_parser.add_argument("--interval-seconds", type=int, default=86400)
    schedule_parser.add_argument("--max-runs", type=int, default=1)
    schedule_parser.add_argument("--metrics-output", type=Path, default=Path("data/metrics/latest_scheduled_ingestion.json"))

    search_parser = subparsers.add_parser("search", help="Search indexed documents")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)

    report_parser = subparsers.add_parser("report", help="Generate a Markdown intelligence digest")
    report_parser.add_argument("--output", type=Path, default=Path("Research_Digest.md"))

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark manifest ingestion performance")
    benchmark_parser.add_argument("manifest", type=Path)
    benchmark_parser.add_argument("--iterations", type=int, default=3)
    benchmark_parser.add_argument("--output", type=Path, default=Path("data/metrics/benchmark.json"))

    answer_parser = subparsers.add_parser("answer", help="Answer a financial analysis question with document citations")
    answer_parser.add_argument("question")
    answer_parser.add_argument("--limit", type=int, default=5)

    subparsers.add_parser("reindex", help="Rebuild document and chunk embeddings from stored document metadata")

    args = parser.parse_args()
    if args.command == "ingest":
        result = build_pipeline().ingest_manifest(args.manifest)
        write_pipeline_metrics(result, args.metrics_output)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.command == "schedule":
        results = run_scheduled_ingestion(args.manifest, args.metrics_output, args.interval_seconds, args.max_runs)
        print(json.dumps({"runs": len(results), "latest": results[-1].to_dict() if results else None}, indent=2))
    elif args.command == "search":
        results = build_vector_store().search(args.query, args.limit)
        print(json.dumps(results, indent=2))
    elif args.command == "report":
        documents = build_metadata_repository().list_documents()
        write_report(documents, args.output)
        print(json.dumps({"report": str(args.output), "documents": len(documents)}, indent=2))
    elif args.command == "benchmark":
        result = run_ingestion_benchmark(args.manifest, args.iterations)
        write_benchmark(result, args.output)
        print(json.dumps(result, indent=2))
    elif args.command == "answer":
        result = build_analysis_service().answer_question(args.question, args.limit)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.command == "reindex":
        result = rebuild_vector_index(build_metadata_repository(), build_vector_store())
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
