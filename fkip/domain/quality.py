from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from fkip.domain.models import DocumentSource, FinancialDocument


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)


def validate_source(source: DocumentSource) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if not source.uri.strip():
        issues.append(ValidationIssue("uri", "Document URI is required."))
    elif source.uri.startswith(("http://", "https://")):
        parsed = urlparse(source.uri)
        if not parsed.netloc:
            issues.append(ValidationIssue("uri", "HTTP document URI must include a host."))
    elif not Path(source.uri).exists():
        issues.append(ValidationIssue("uri", "Local document path does not exist."))

    if source.title is not None and len(source.title.strip()) < 3:
        issues.append(ValidationIssue("title", "Document title must be at least three characters."))

    if source.published_at is not None:
        try:
            date.fromisoformat(source.published_at)
        except ValueError:
            issues.append(ValidationIssue("published_at", "Published date must use YYYY-MM-DD format."))

    return ValidationResult(valid=not any(issue.severity == "error" for issue in issues), issues=issues)


def validate_document(document: FinancialDocument, min_text_chars: int = 80) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if len(document.raw_text.strip()) < min_text_chars:
        issues.append(ValidationIssue("raw_text", f"Extracted text must contain at least {min_text_chars} characters."))
    if not document.title.strip():
        issues.append(ValidationIssue("title", "Resolved document title is required."))
    if document.issuer is not None and len(document.issuer.strip()) < 2:
        issues.append(ValidationIssue("issuer", "Issuer must contain at least two characters."))
    return ValidationResult(valid=not any(issue.severity == "error" for issue in issues), issues=issues)


def canonical_source_key(source: DocumentSource) -> str:
    uri = source.uri.strip()
    if uri.startswith(("http://", "https://")):
        parsed = urlparse(uri)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".lower()
    return str(Path(uri).resolve()).lower()

