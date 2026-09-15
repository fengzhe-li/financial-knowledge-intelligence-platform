from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from urllib.request import Request, urlopen
from typing import Protocol

from fkip.infrastructure.metadata_repository import MetadataRepository
from fkip.infrastructure.vector_store import VectorStore


@dataclass(frozen=True)
class Citation:
    document_id: str
    title: str
    issuer: str | None
    uri: str
    chunk_id: str
    chunk_index: int
    score: float
    excerpt: str


@dataclass(frozen=True)
class FinancialAnalysisAnswer:
    question: str
    answer: str
    citations: list[Citation]
    retrieval_count: int

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "retrieval_count": self.retrieval_count,
            "citations": [asdict(citation) for citation in self.citations],
        }


class LlmSummariser(Protocol):
    def summarise(self, question: str, citations: list[Citation]) -> str:
        ...


class ExtractiveFinancialSummariser:
    def summarise(self, question: str, citations: list[Citation]) -> str:
        if not citations:
            return "No relevant financial document evidence was found for this question."

        lines = [
            "Based on the retrieved financial document evidence:",
        ]
        for index, citation in enumerate(citations[:3], start=1):
            lines.append(f"{index}. {citation.excerpt} [{index}]")
        lines.append("This answer is extractive and limited to the cited documents.")
        return " ".join(lines)


@dataclass(frozen=True)
class OpenAiFinancialSummariser:
    api_key: str
    model: str
    timeout_seconds: int = 30

    def summarise(self, question: str, citations: list[Citation]) -> str:
        if not citations:
            return "No relevant financial document evidence was found for this question."

        evidence = "\n\n".join(
            f"[{index}] Title: {citation.title}\nIssuer: {citation.issuer or 'Unknown'}\nExcerpt: {citation.excerpt}"
            for index, citation in enumerate(citations, start=1)
        )
        prompt = (
            "You are producing a concise financial document analysis answer. "
            "Use only the supplied evidence. Include bracketed citation numbers for every claim. "
            "If the evidence is insufficient, say so clearly.\n\n"
            f"Question: {question}\n\nEvidence:\n{evidence}"
        )
        payload = json.dumps({"model": self.model, "input": prompt}).encode("utf-8")
        request = Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        return _extract_response_text(data)


class FinancialAnalysisService:
    def __init__(
        self,
        vector_store: VectorStore,
        metadata_repository: MetadataRepository,
        summariser: LlmSummariser | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.metadata_repository = metadata_repository
        self.summariser = summariser or ExtractiveFinancialSummariser()

    def answer_question(self, question: str, limit: int = 5) -> FinancialAnalysisAnswer:
        retrieved = self.vector_store.search_chunks(question, limit=limit)
        citations: list[Citation] = []
        for item in retrieved:
            document = self.metadata_repository.get(item["document_id"])
            if document is None:
                continue
            citations.append(
                Citation(
                    document_id=document.document_id,
                    title=document.title,
                    issuer=document.issuer,
                    uri=document.uri,
                    chunk_id=item["chunk_id"],
                    chunk_index=item["chunk_index"],
                    score=item["score"],
                    excerpt=_clean_excerpt(item["text"]),
                )
            )
        answer = self.summariser.summarise(question, citations)
        return FinancialAnalysisAnswer(question=question, answer=answer, citations=citations, retrieval_count=len(citations))


def _clean_excerpt(text: str, max_chars: int = 420) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def _extract_response_text(data: dict) -> str:
    if data.get("output_text"):
        return str(data["output_text"])
    chunks: list[str] = []
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(str(content["text"]))
    return "\n".join(chunks).strip() or "The LLM provider returned no text."
