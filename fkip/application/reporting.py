from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from fkip.domain.models import ProcessedDocument


def build_markdown_report(documents: list[ProcessedDocument]) -> str:
    grouped: dict[str, list[ProcessedDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.source_type.value].append(document)

    lines = [
        "# Financial Knowledge Intelligence Digest",
        "",
        f"Generated at: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
        "## Executive Summary",
        "",
        f"- Documents indexed: {len(documents)}",
        f"- Source categories: {len(grouped)}",
        "",
        "## Intelligence by Source Type",
        "",
    ]
    for source_type, items in sorted(grouped.items()):
        lines.append(f"### {source_type.replace('_', ' ').title()}")
        lines.append("")
        for item in items:
            lines.extend(
                [
                    f"#### {item.title}",
                    f"- Issuer: {item.issuer or 'Unknown'}",
                    f"- Topics: {', '.join(item.topics)}",
                    f"- Keywords: {', '.join(item.keywords)}",
                    f"- Summary: {item.summary}",
                    "",
                ]
            )
    return "\n".join(lines)


def write_report(documents: list[ProcessedDocument], output_path: Path) -> None:
    output_path.write_text(build_markdown_report(documents), encoding="utf-8")

