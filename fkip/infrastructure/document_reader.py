import ipaddress
import socket
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def validate_url_for_ssrf(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a valid hostname.")
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve host '{hostname}': {exc}") from exc

    for item in addr_info:
        ip_str = item[4][0]
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
            raise ValueError(f"Access to restricted or private IP address '{ip_str}' is forbidden for SSRF safety.")


def read_document_text(uri: str) -> str:
    if uri.startswith(("http://", "https://")):
        validate_url_for_ssrf(uri)
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
