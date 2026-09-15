# Financial Document Dataset Pipeline

This project includes a realistic public financial document collection pipeline designed to build a 500+ document dataset for ingestion, search and reporting.

## Primary Public Source

The first dataset source is **SEC EDGAR**, the public filing system for companies that file with the U.S. Securities and Exchange Commission.

Useful SEC pages:

- SEC EDGAR search and public filings: `https://www.sec.gov/search-filings`
- SEC data APIs: `https://data.sec.gov/`
- SEC fair-access guidance: `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`

EDGAR is used because it is:

- Publicly accessible
- Large enough to support 500+ documents
- Structured enough for repeatable collection
- Realistic for financial document search use cases
- Suitable for annual reports, quarterly reports and public financial disclosures

## Collected Document Types

The collector supports SEC form filtering. The recommended starting forms are:

- `10-K`: annual reports
- `10-Q`: quarterly public reports

Optional extensions:

- `8-K`: current reports
- `20-F`: annual reports for foreign private issuers
- `40-F`: annual reports for certain Canadian issuers

## 500+ Document Target

The seed file `config/sec_tickers_large_cap.txt` contains 100 large public-company tickers. With a per-company limit of 6 recent filings, the collector can target 500+ documents:

```bash
python3 scripts/collect_sec_filings.py \
  --user-agent "Your Name your.email@example.com" \
  --tickers-file config/sec_tickers_large_cap.txt \
  --forms 10-K,10-Q \
  --max-documents 500 \
  --per-company-limit 6 \
  --request-delay-seconds 0.2 \
  --output-root data/raw/sec \
  --manifest-output data/manifests/sec_financial_documents.json \
  --metadata-output data/metadata/sec_documents.jsonl
```

The `--request-delay-seconds 0.2` setting keeps the collector around five requests per second, below the SEC fair-access maximum of 10 requests per second.

## Outputs

The collector writes three dataset artifacts:

```text
data/raw/sec/                               Downloaded SEC filing documents
data/manifests/sec_financial_documents.json Platform ingestion manifest
data/metadata/sec_documents.jsonl           Rich collection metadata
```

The ingestion manifest uses the platform's existing schema:

```json
{
  "uri": "data/raw/sec/AAPL/10-K/2025-10-31_000032019325000079_aapl-20250927.htm",
  "source_type": "annual_report",
  "title": "Apple Inc. 10-K filing (2025-10-31)",
  "issuer": "Apple Inc.",
  "published_at": "2025-10-31"
}
```

The metadata JSONL file stores collection-specific audit fields:

```json
{
  "ticker": "AAPL",
  "cik": "0000320193",
  "company_name": "Apple Inc.",
  "form_type": "10-K",
  "filing_date": "2025-10-31",
  "report_date": "2025-09-27",
  "accession_number": "0000320193-25-000079",
  "primary_document": "aapl-20250927.htm",
  "sec_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
  "local_path": "data/raw/sec/AAPL/10-K/2025-10-31_000032019325000079_aapl-20250927.htm",
  "source_type": "annual_report",
  "file_size_bytes": 1250000
}
```

## Batch Ingestion

After collection, ingest the full generated manifest:

```bash
python3 -m fkip.cli ingest data/manifests/sec_financial_documents.json \
  --metrics-output data/metrics/sec_ingestion_metrics.json
```

The platform will:

- Validate local files and metadata
- Skip duplicate source URIs
- Extract text from HTML filings
- Classify finance topics
- Persist metadata
- Store raw text in object storage
- Update the vector search index
- Write run-level metrics

## Dataset Statistics

Generate dataset statistics after collection:

```bash
python3 scripts/generate_dataset_statistics.py \
  --manifest data/manifests/sec_financial_documents.json \
  --metadata data/metadata/sec_documents.jsonl \
  --json-output data/metrics/dataset_statistics.json \
  --markdown-output data/metrics/dataset_statistics.md
```

The statistics include:

- Total documents
- Unique issuers
- Unique source URIs
- Source type counts
- SEC form type counts
- Top issuers
- Documents by year
- File extensions
- Downloaded file size totals
- Missing metadata count

## Dry Run

Use `--dry-run` to inspect how many candidate documents would be selected without downloading filings:

```bash
python3 scripts/collect_sec_filings.py \
  --user-agent "Your Name your.email@example.com" \
  --max-documents 25 \
  --per-company-limit 3 \
  --dry-run
```

Dry-run manifests are useful for auditing selected companies/forms, but they are not ingestible until the files are actually downloaded.

## Limitations

- SEC EDGAR focuses on SEC filers, so the dataset is U.S.-heavy rather than UK-only.
- Filing HTML structure varies by issuer and reporting period.
- Some filings include large tables, inline XBRL markup and boilerplate text.
- Text extraction is intentionally lightweight and deterministic; it does not perform table reconstruction.
- Downloaded filings can be large, so a 500-document dataset may require hundreds of MBs or more.
- The collector depends on SEC availability and fair-access policies.
- The script requires a descriptive User-Agent with contact information.
- The initial collector does not yet include FCA, Companies House or London Stock Exchange documents.

## Recommended Next Dataset Extensions

- FCA policy statements and consultation papers
- UK company annual reports from issuer investor-relations pages
- Companies House filing metadata where API credentials are available
- Bank of England publications and speeches
- LSE/RNS announcement metadata

These can reuse the same output contract: downloaded files, ingestion manifest and metadata JSONL.
