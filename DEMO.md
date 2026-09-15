# End-to-End Demo Workflow

This guide shows a clean local demo of the **Financial Knowledge Intelligence Platform** from fresh installation to ingestion, search, report generation and benchmarking.

The demo uses the sample files in `samples/` and stores runtime data in `/tmp/fkip_demo` so it does not pollute the repository.

## 1. Fresh Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/<your-username>/financial-knowledge-intelligence-platform.git
cd financial-knowledge-intelligence-platform
```

For an already-cloned local workspace, start from the project directory:

```bash
cd <project-directory>
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

Expected output:

```text
........s...s...
----------------------------------------------------------------------
Ran 16 tests in 0.017s

OK (skipped=2)
```

## 2. Environment Setup

Use an isolated local SQLite database, object store folder and vector index:

```bash
export DATABASE_URL=sqlite:////tmp/fkip_demo/metadata.db
export OBJECT_STORE_PATH=/tmp/fkip_demo/documents
export VECTOR_INDEX_PATH=/tmp/fkip_demo/index/vector_index.json
export LOG_LEVEL=INFO
```

Optional cleanup before a fresh demo run:

```bash
rm -rf /tmp/fkip_demo
```

The demo data source manifest is:

```bash
samples/financial_sources.json
```

It points to three local sample documents:

- `samples/barclays_annual_report_excerpt.txt`
- `samples/fca_operational_resilience_excerpt.txt`
- `samples/market_news_excerpt.txt`

## 3. Sample Data Ingestion

Run the ingestion pipeline:

```bash
python3 -m fkip.cli ingest samples/financial_sources.json \
  --metrics-output /tmp/fkip_demo/metrics/latest_ingestion.json
```

Expected output includes JSON structured logs followed by a pipeline metrics summary:

```json
{
  "run_id": "manifest:samples/financial_sources.json",
  "duration_seconds": 0.0034,
  "sources_seen": 3,
  "documents_ingested": 3,
  "documents_skipped": 0,
  "duplicate_sources": 0,
  "validation_failures": 0,
  "errors": [],
  "document_ids": [
    "91e13397-1cc1-570c-aa66-ab3a586bf23a",
    "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6",
    "cd24c608-c7e4-5757-8a77-8358ef01a827"
  ]
}
```

Expected generated runtime artifacts:

```text
/tmp/fkip_demo/metadata.db
/tmp/fkip_demo/documents/
/tmp/fkip_demo/index/vector_index.json
/tmp/fkip_demo/metrics/latest_ingestion.json
```

## 4. Search Example

Search for FCA operational resilience content:

```bash
python3 -m fkip.cli search "operational resilience fca" --limit 2
```

Expected output:

```json
[
  {
    "document_id": "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6",
    "title": "FCA Operational Resilience Excerpt",
    "summary": "The FCA expects firms to identify important business services, set impact tolerances and maintain evidence that they can remain within those tolerances during severe but plausible disruption. Financial institutions should improve governance, incident response, third-party risk management and cyber resilience across critical technology services.",
    "topics": [
      "Risk & Compliance",
      "Technology & Operations",
      "ESG & Sustainability"
    ],
    "score": 0.165
  },
  {
    "document_id": "91e13397-1cc1-570c-aa66-ab3a586bf23a",
    "title": "Barclays Annual Report Excerpt",
    "topics": [
      "Technology & Operations",
      "Risk & Compliance"
    ],
    "score": 0.1491
  }
]
```

The highest ranked result should be the FCA operational resilience document, demonstrating that the retrieval layer is using indexed document content rather than only file names.

## 5. Report Generation Example

Generate a Markdown intelligence digest:

```bash
python3 -m fkip.cli report --output /tmp/fkip_demo/Research_Digest.md
```

Expected command output:

```json
{
  "report": "/tmp/fkip_demo/Research_Digest.md",
  "documents": 3
}
```

Preview the report:

```bash
sed -n '1,120p' /tmp/fkip_demo/Research_Digest.md
```

Expected report text:

```markdown
# Financial Knowledge Intelligence Digest

Generated at: 2026-08-17T01:55:21Z

## Executive Summary

- Documents indexed: 3
- Source categories: 3

## Intelligence by Source Type

### Annual Report

#### Barclays Annual Report Excerpt
- Issuer: Barclays PLC
- Topics: Technology & Operations, Risk & Compliance
- Keywords: income, barclays, reported, resilient, performance, across, its, consumer
- Summary: Barclays reported resilient income performance across its UK consumer and corporate banking divisions. The annual report highlighted net interest income, capital discipline, liquidity coverage and operational resilience. Management noted that cloud modernisation and data platform investment remain important for risk analytics, cyber controls and customer service automation.

### Fca Regulatory

#### FCA Operational Resilience Excerpt
- Issuer: Financial Conduct Authority
- Topics: Risk & Compliance, Technology & Operations, ESG & Sustainability
- Keywords: services, tolerances, fca, expects, firms, identify, important, business
- Summary: The FCA expects firms to identify important business services, set impact tolerances and maintain evidence that they can remain within those tolerances during severe but plausible disruption. Financial institutions should improve governance, incident response, third-party risk management and cyber resilience across critical technology services.
```

The generated timestamp will differ on each run.

## 6. Traceable RAG Analysis Example

Ask a financial document question with citations:

```bash
python3 -m fkip.cli answer "What does the FCA say about operational resilience?" --limit 3
```

Expected output shape:

```json
{
  "question": "What does the FCA say about operational resilience?",
  "answer": "Based on the retrieved financial document evidence: ... [1]",
  "retrieval_count": 3,
  "citations": [
    {
      "title": "FCA Operational Resilience Excerpt",
      "issuer": "Financial Conduct Authority",
      "uri": "samples/fca_operational_resilience_excerpt.txt",
      "chunk_id": "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6:0",
      "score": 0.1943,
      "excerpt": "The FCA expects firms to identify important business services..."
    }
  ]
}
```

Rebuild embeddings for existing ingested documents:

```bash
python3 -m fkip.cli reindex
```

## 7. Benchmark Example

Run a small local ingestion benchmark:

```bash
python3 -m fkip.cli benchmark samples/financial_sources.json \
  --iterations 3 \
  --output /tmp/fkip_demo/metrics/benchmark.json
```

Expected output:

```json
{
  "manifest": "samples/financial_sources.json",
  "iterations": 3,
  "environment": "local",
  "documents_processed": 9,
  "mean_duration_seconds": 0.0024,
  "min_duration_seconds": 0.0019,
  "max_duration_seconds": 0.0032,
  "throughput_docs_per_second": 1244.8565
}
```

Exact timings will vary by machine. The important fields for a demo are:

- `documents_processed`
- `mean_duration_seconds`
- `throughput_docs_per_second`

## 8. API Demo Option

Start the FastAPI service:

```bash
uvicorn fkip.interfaces.api.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected output:

```json
{
  "status": "ok",
  "service": "Financial Knowledge Intelligence Platform"
}
```

Search through the API:

```bash
curl "http://localhost:8000/search?q=operational%20resilience%20fca&limit=2"
```

Expected output shape:

```json
[
  {
    "document_id": "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6",
    "title": "FCA Operational Resilience Excerpt",
    "topics": ["Risk & Compliance", "Technology & Operations", "ESG & Sustainability"],
    "score": 0.165
  }
]
```

Generate a cited financial answer through the API:

```bash
curl -X POST http://localhost:8000/analysis/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the FCA say about operational resilience?", "limit": 3}'
```

## Demo Talking Points

Use this workflow to explain the platform as a production-style data system:

- Ingestion is repeatable and idempotent.
- Validation prevents bad documents from entering the index.
- Metrics record processed, skipped, duplicate and failed documents.
- Search uses indexed content and returns ranked results.
- Reporting converts indexed metadata into a stakeholder-readable digest.
- Benchmarking provides a baseline for scaling to larger document batches.
