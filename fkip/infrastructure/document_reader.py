from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


def read_document_text(uri: str) -> str:
    if uri.startswith(("http://", "https://")):
        request = Request(uri, headers={"User-Agent": "financial-knowledge-intelligence/1.0"})
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            payload = response.read()
        if "pdf" in content_type or uri.lower().endswith(".pdf"):
            return _read_pdf_bytes(payload)
        decoded = payload.decode("utf-8", errors="ignore")
        if "html" in content_type or uri.lower().endswith((".html", ".htm")):
            return _strip_html(decoded)
        return decoded

    path = Path(uri)
    if path.suffix.lower() == ".pdf":
        return _read_pdf_path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".html", ".htm"}:
        return _strip_html(text)
    return text


def _read_pdf_path(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to ingest PDF documents.") from exc

    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_pdf_bytes(payload: bytes) -> str:
    try:
        from io import BytesIO

        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to ingest PDF documents.") from exc

    reader = PdfReader(BytesIO(payload))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_tag_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_tag_depth > 0:
            self._ignored_tag_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_tag_depth == 0:
            clean = data.strip()
            if clean:
                self._chunks.append(clean)

    def text(self) -> str:
        return " ".join(self._chunks)


def _strip_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return parser.text()
