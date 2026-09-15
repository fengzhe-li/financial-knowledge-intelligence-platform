from __future__ import annotations

import argparse
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}"

FORM_SOURCE_TYPES = {
    "10-K": "annual_report",
    "10-K/A": "annual_report",
    "20-F": "annual_report",
    "40-F": "annual_report",
    "10-Q": "public_report",
    "10-Q/A": "public_report",
    "8-K": "public_report",
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SecFilingDocument:
    ticker: str
    cik: str
    company_name: str
    form_type: str
    filing_date: str
    report_date: str | None
    accession_number: str
    primary_document: str
    sec_url: str
    local_path: str
    source_type: str
    title: str
    issuer: str
    published_at: str
    file_size_bytes: int

    def to_manifest_item(self) -> dict:
        return {
            "uri": self.local_path,
            "source_type": self.source_type,
            "title": self.title,
            "issuer": self.issuer,
            "published_at": self.published_at,
        }


def load_seed_tickers(path: Path) -> list[str]:
    tickers: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip().upper()
        if clean and not clean.startswith("#"):
            tickers.append(clean)
    return tickers


def fetch_json(url: str, user_agent: str) -> dict:
    request = Request(url, headers=_headers(user_agent))
    with urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def download_bytes(url: str, user_agent: str) -> bytes:
    request = Request(url, headers=_headers(user_agent))
    with urlopen(request, timeout=60) as response:
        return response.read()


def build_ticker_lookup(user_agent: str) -> dict[str, dict]:
    raw = fetch_json(SEC_TICKERS_URL, user_agent)
    return {
        str(item["ticker"]).upper(): {
            "cik": str(item["cik_str"]).zfill(10),
            "title": item["title"],
        }
        for item in raw.values()
    }


def collect_sec_filings(
    tickers_file: Path,
    output_root: Path,
    manifest_output: Path,
    metadata_output: Path,
    user_agent: str,
    forms: set[str],
    max_documents: int,
    per_company_limit: int,
    request_delay_seconds: float,
    dry_run: bool = False,
) -> list[SecFilingDocument]:
    tickers = load_seed_tickers(tickers_file)
    ticker_lookup = build_ticker_lookup(user_agent)
    documents: list[SecFilingDocument] = []

    output_root.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        if len(documents) >= max_documents:
            break
        if ticker not in ticker_lookup:
            logger.warning("ticker_not_found", extra={"ticker": ticker})
            continue

        company = ticker_lookup[ticker]
        cik = company["cik"]
        company_name = company["title"]
        try:
            submissions = fetch_json(SEC_SUBMISSIONS_URL.format(cik=cik), user_agent)
        except (HTTPError, URLError, TimeoutError) as exc:
            logger.warning("submissions_fetch_failed", extra={"ticker": ticker, "error": str(exc)})
            continue
        time.sleep(request_delay_seconds)

        recent = submissions.get("filings", {}).get("recent", {})
        company_documents = _documents_from_recent_filings(
            ticker=ticker,
            cik=cik,
            company_name=company_name,
            recent=recent,
            forms=forms,
            output_root=output_root,
            limit=min(per_company_limit, max_documents - len(documents)),
        )

        for document in company_documents:
            if len(documents) >= max_documents:
                break
            if not dry_run:
                try:
                    payload = download_bytes(document.sec_url, user_agent)
                except (HTTPError, URLError, TimeoutError) as exc:
                    logger.warning("filing_download_failed", extra={"ticker": ticker, "url": document.sec_url, "error": str(exc)})
                    continue
                local_path = Path(document.local_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(payload)
                document = SecFilingDocument(**{**asdict(document), "file_size_bytes": len(payload)})
                time.sleep(request_delay_seconds)
            documents.append(document)
            logger.info("filing_collected", extra={"ticker": ticker, "form_type": document.form_type, "local_path": document.local_path})

    _write_manifest(documents, manifest_output)
    _write_metadata(documents, metadata_output)
    return documents


def _documents_from_recent_filings(
    ticker: str,
    cik: str,
    company_name: str,
    recent: dict,
    forms: set[str],
    output_root: Path,
    limit: int,
) -> list[SecFilingDocument]:
    documents: list[SecFilingDocument] = []
    form_values = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])

    for index, form_type in enumerate(form_values):
        if len(documents) >= limit:
            break
        if form_type not in forms:
            continue
        primary_document = _safe_index(primary_documents, index)
        accession_number = _safe_index(accessions, index)
        filing_date = _safe_index(filing_dates, index)
        if not primary_document or not accession_number or not filing_date:
            continue

        accession_no_dashes = accession_number.replace("-", "")
        sec_url = SEC_ARCHIVE_URL.format(
            cik=str(int(cik)),
            accession_no_dashes=accession_no_dashes,
            primary_document=primary_document,
        )
        safe_doc_name = _safe_filename(primary_document)
        local_path = output_root / ticker / form_type.replace("/", "-") / f"{filing_date}_{accession_no_dashes}_{safe_doc_name}"
        source_type = FORM_SOURCE_TYPES.get(form_type, "public_report")
        title = f"{company_name} {form_type} filing ({filing_date})"
        documents.append(
            SecFilingDocument(
                ticker=ticker,
                cik=cik,
                company_name=company_name,
                form_type=form_type,
                filing_date=filing_date,
                report_date=_safe_index(report_dates, index) or None,
                accession_number=accession_number,
                primary_document=primary_document,
                sec_url=sec_url,
                local_path=str(local_path),
                source_type=source_type,
                title=title,
                issuer=company_name,
                published_at=filing_date,
                file_size_bytes=0,
            )
        )
    return documents


def _safe_index(values: list, index: int) -> str:
    if index >= len(values):
        return ""
    return str(values[index] or "")


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)[:180]


def _write_manifest(documents: list[SecFilingDocument], output_path: Path) -> None:
    output_path.write_text(json.dumps([document.to_manifest_item() for document in documents], indent=2), encoding="utf-8")


def _write_metadata(documents: list[SecFilingDocument], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(asdict(document)) + "\n")


def _headers(user_agent: str) -> dict[str, str]:
    return {
        "User-Agent": user_agent,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public SEC EDGAR financial filings for FKIP ingestion.")
    parser.add_argument("--tickers-file", type=Path, default=Path("config/sec_tickers_large_cap.txt"))
    parser.add_argument("--output-root", type=Path, default=Path("data/raw/sec"))
    parser.add_argument("--manifest-output", type=Path, default=Path("data/manifests/sec_financial_documents.json"))
    parser.add_argument("--metadata-output", type=Path, default=Path("data/metadata/sec_documents.jsonl"))
    parser.add_argument("--user-agent", required=True, help="Required by SEC fair-access guidance. Use 'Name email@example.com'.")
    parser.add_argument("--forms", default="10-K,10-Q", help="Comma-separated SEC form types to collect.")
    parser.add_argument("--max-documents", type=int, default=500)
    parser.add_argument("--per-company-limit", type=int, default=6)
    parser.add_argument("--request-delay-seconds", type=float, default=0.2)
    parser.add_argument("--dry-run", action="store_true", help="Build manifest/metadata without downloading filing documents.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    forms = {form.strip().upper() for form in args.forms.split(",") if form.strip()}
    documents = collect_sec_filings(
        tickers_file=args.tickers_file,
        output_root=args.output_root,
        manifest_output=args.manifest_output,
        metadata_output=args.metadata_output,
        user_agent=args.user_agent,
        forms=forms,
        max_documents=args.max_documents,
        per_company_limit=args.per_company_limit,
        request_delay_seconds=args.request_delay_seconds,
        dry_run=args.dry_run,
    )
    print(
        json.dumps(
            {
                "documents_collected": len(documents),
                "manifest": str(args.manifest_output),
                "metadata": str(args.metadata_output),
                "output_root": str(args.output_root),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
