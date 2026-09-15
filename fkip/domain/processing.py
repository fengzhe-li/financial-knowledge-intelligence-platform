from __future__ import annotations

import re
from collections import Counter

from fkip.domain.models import FinancialDocument, ProcessedDocument


FINANCIAL_TOPICS: dict[str, list[str]] = {
    "Corporate Performance": ["revenue", "profit", "margin", "earnings", "dividend", "cash flow"],
    "Risk & Compliance": ["risk", "capital", "liquidity", "compliance", "regulatory", "fca"],
    "Markets & Macro": ["inflation", "interest rate", "market", "bond", "equity", "forex"],
    "ESG & Sustainability": ["climate", "emissions", "sustainability", "governance", "social"],
    "Technology & Operations": ["platform", "cloud", "cyber", "data", "automation", "resilience"],
}

STOP_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "between",
    "from",
    "into",
    "over",
    "that",
    "the",
    "their",
    "there",
    "this",
    "through",
    "with",
    "within",
}


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\S\r\n]+", " ", text)
    return text.strip()


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
    counts = Counter(token for token in tokens if token not in STOP_WORDS)
    return [token for token, _ in counts.most_common(limit)]


def classify_topics(text: str) -> list[str]:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for topic, terms in FINANCIAL_TOPICS.items():
        scores[topic] = sum(lowered.count(term) for term in terms)

    ranked = [topic for topic, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score > 0]
    return ranked[:3] or ["General Financial Intelligence"]


def summarise_text(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return " ".join(sentence for sentence in sentences[:max_sentences] if sentence)


def process_document(document: FinancialDocument, object_key: str) -> ProcessedDocument:
    from datetime import UTC, datetime

    normalized = clean_text(document.raw_text)
    return ProcessedDocument(
        document_id=document.document_id,
        title=document.title,
        source_type=document.source_type,
        issuer=document.issuer,
        published_at=document.published_at,
        uri=document.uri,
        object_key=object_key,
        clean_text=normalized,
        summary=summarise_text(normalized),
        keywords=extract_keywords(normalized),
        topics=classify_topics(normalized),
        created_at=datetime.now(UTC),
    )
