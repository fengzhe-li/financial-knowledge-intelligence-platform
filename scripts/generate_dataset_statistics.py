from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def generate_statistics(manifest_path: Path, metadata_path: Path | None = None) -> dict:
    manifest = load_json(manifest_path)
    metadata = load_jsonl(metadata_path) if metadata_path else []
    metadata_by_uri = {record.get("local_path"): record for record in metadata}

    source_types = Counter(item.get("source_type", "unknown") for item in manifest)
    issuers = Counter(item.get("issuer", "unknown") for item in manifest)
    years = Counter(str(item.get("published_at", "unknown"))[:4] for item in manifest)
    forms = Counter(record.get("form_type", "unknown") for record in metadata)
    tickers = Counter(record.get("ticker", "unknown") for record in metadata)
    extensions = Counter(Path(item.get("uri", "")).suffix.lower() or "none" for item in manifest)
    file_sizes = [int(record.get("file_size_bytes", 0)) for record in metadata if int(record.get("file_size_bytes", 0)) > 0]

    return {
        "manifest": str(manifest_path),
        "metadata": str(metadata_path) if metadata_path else None,
        "total_documents": len(manifest),
        "unique_issuers": len(issuers),
        "unique_source_uris": len({item.get("uri") for item in manifest}),
        "source_types": dict(source_types.most_common()),
        "form_types": dict(forms.most_common()),
        "top_issuers": dict(issuers.most_common(20)),
        "top_tickers": dict(tickers.most_common(20)),
        "documents_by_year": dict(sorted(years.items())),
        "file_extensions": dict(extensions.most_common()),
        "downloaded_file_size_bytes": {
            "total": sum(file_sizes),
            "min": min(file_sizes) if file_sizes else 0,
            "max": max(file_sizes) if file_sizes else 0,
            "mean": round(sum(file_sizes) / len(file_sizes), 2) if file_sizes else 0,
        },
        "missing_metadata_records": sum(1 for item in manifest if item.get("uri") not in metadata_by_uri) if metadata else 0,
    }


def write_markdown_statistics(statistics: dict, output_path: Path) -> None:
    lines = [
        "# Financial Document Dataset Statistics",
        "",
        f"- Total documents: {statistics['total_documents']}",
        f"- Unique issuers: {statistics['unique_issuers']}",
        f"- Unique source URIs: {statistics['unique_source_uris']}",
        "",
        "## Source Types",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in statistics["source_types"].items())
    lines.extend(["", "## Form Types", ""])
    lines.extend(f"- {key}: {value}" for key, value in statistics["form_types"].items())
    lines.extend(["", "## Documents by Year", ""])
    lines.extend(f"- {key}: {value}" for key, value in statistics["documents_by_year"].items())
    lines.extend(["", "## Top Issuers", ""])
    lines.extend(f"- {key}: {value}" for key, value in statistics["top_issuers"].items())
    lines.extend(["", "## Downloaded File Sizes", ""])
    for key, value in statistics["downloaded_file_size_bytes"].items():
        lines.append(f"- {key}: {value}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dataset statistics for FKIP financial document manifests.")
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/sec_financial_documents.json"))
    parser.add_argument("--metadata", type=Path, default=Path("data/metadata/sec_documents.jsonl"))
    parser.add_argument("--json-output", type=Path, default=Path("data/metrics/dataset_statistics.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("data/metrics/dataset_statistics.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    statistics = generate_statistics(args.manifest, args.metadata)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(statistics, indent=2), encoding="utf-8")
    write_markdown_statistics(statistics, args.markdown_output)
    print(json.dumps(statistics, indent=2))


if __name__ == "__main__":
    main()
