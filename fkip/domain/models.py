from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class SourceType(str, Enum):
    ANNUAL_REPORT = "annual_report"
    FINANCIAL_NEWS = "financial_news"
    FCA_REGULATORY = "fca_regulatory"
    PUBLIC_REPORT = "public_report"
    RESEARCH = "research"


@dataclass(frozen=True)
class DocumentSource:
    uri: str
    source_type: SourceType
    title: str | None = None
    issuer: str | None = None
    published_at: str | None = None


@dataclass
class FinancialDocument:
    title: str
    source_type: SourceType
    raw_text: str
    uri: str
    issuer: str | None = None
    published_at: str | None = None
    document_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessedDocument:
    document_id: str
    title: str
    source_type: SourceType
    issuer: str | None
    published_at: str | None
    uri: str
    object_key: str
    clean_text: str
    summary: str
    keywords: list[str]
    topics: list[str]
    created_at: datetime

