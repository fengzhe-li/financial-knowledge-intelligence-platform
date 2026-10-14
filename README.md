# Financial Knowledge Intelligence Platform

A production-style FinTech data platform for ingesting, validating, processing, indexing and searching financial documents such as annual reports, regulatory publications, market news and public filings.

The project demonstrates backend and data engineering skills relevant to UK FinTech roles: FastAPI service design, batch ingestion, data quality checks, PostgreSQL metadata persistence, Qdrant vector retrieval, Docker deployment, CI checks and traceable document analysis.

Key engineering challenges covered:

- Repeatable financial document ingestion from manifests and public filing collectors.
- Validation, duplicate detection, lineage records and run-level processing metrics.
- Separation of metadata storage, raw document storage and semantic retrieval indexes.
- Thin API and dashboard interfaces over reusable application services.
- Deterministic cited retrieval by default, with optional LLM summarisation kept inside the RAG layer.

Detailed supporting docs:

- [Architecture](docs/ARCHITECTURE.md)
- [Interview notes](docs/INTERVIEW_NOTES.md)
- [Benchmark and validation report](docs/BENCHMARK.md)
- [End-to-end demo](DEMO.md)
- [Dataset pipeline](docs/DATASET.md)

## Evidence-First Web Research Workspace

The platform features a modern, evidence-first financial research workspace built with **React 19 + TypeScript + Vite**, styled with a high-contrast dark FinTech design system and directly powered by the authoritative FastAPI backend.

### Key Capabilities

1. **Research Overview Dashboard**: Real-time telemetry, verified indexed document counts, source type & year distributions, and recent ingestion summaries.
2. **Financial Document Explorer**: Multi-facet catalog search (issuer, source type, publication date), paginated tabular browsing, and detailed modal inspection with full metadata and indexed vector chunk inspection.
3. **Evidence-Based AI Research**: Natural-language financial Q&A powered by deterministic extractive RAG, interactive numbered citations `[#]`, and a slide-out passage inspector drawer revealing exact text, relevance scores, and provenance.
4. **Side-by-Side Company Comparison**: Isolated multi-issuer disclosure analysis on critical topics (Cybersecurity, Operational Resilience, Regulatory Compliance), explicit evidence gap reporting, and objective neutral observations.
5. **Pipeline Operations & Lineage Ledger**: Full operational observability showing run-level processing duration, validation failures, skipped duplicates, and persistent audit records.

### Interface Previews

| Research Overview Dashboard | Document Explorer & Provenance |
| :---: | :---: |
| ![Research Overview](docs/images/screenshot_01_research_overview.png) | ![Document Explorer](docs/images/screenshot_02_document_explorer.png) |

| Evidence-Based AI Research with Expanded Citation | Side-by-Side Company Comparison |
| :---: | :---: |
| ![AI Research](docs/images/screenshot_03_ai_research_expanded_citation.png) | ![Company Comparison](docs/images/screenshot_04_company_comparison.png) |

| Pipeline Operations & Run Ledger |
| :---: |
| ![Pipeline Operations](docs/images/screenshot_05_pipeline_operations.png) |


## Current Architecture Analysis

The original **Telecom Research Intelligence** project was a compact batch pipeline:

- `fetch_arxiv.py` collected research PDFs from arXiv.
- `read_pdf.py` tested PDF text extraction.
- `summarize.py` cleaned document text, extracted keywords and classified topics.
- `results.json` acted as the structured knowledge base.
- `generate_report.py` produced a Markdown digest.

Original data flow:

```text
arXiv API -> PDFs -> PDF text extraction -> keyword/topic analysis -> results.json -> Markdown digest
```

The useful engineering pattern was kept, but the implementation has been split into clear domain, application, infrastructure and interface layers. The platform is now designed around financial documents, data quality, repeatable orchestration and operational visibility.

## What Was Reused

- Unstructured document ingestion
- PDF and text extraction
- Cleaning and normalisation
- Keyword extraction
- Topic classification
- Structured metadata output
- Searchable knowledge base
- Markdown intelligence digest generation
- Repeatable CLI pipeline execution

## System Architecture

![System Architecture](docs/images/system_architecture.svg)

```mermaid
flowchart TB
    subgraph Sources["Financial Data Sources"]
        Annual["Annual Reports"]
        FCA["FCA Documents"]
        News["Financial News"]
        Reports["Public Reports"]
    end

    subgraph Orchestration["Pipeline Orchestration"]
        CLI["CLI Runner"]
        Scheduler["Scheduled Runner"]
        Airflow["Airflow DAG"]
    end

    subgraph Application["Application Services"]
        Pipeline["Ingestion Pipeline"]
        Quality["Data Quality Layer"]
        Processing["Processing Service"]
        Analysis["RAG Analysis Service"]
        Reporting["Digest Reporting"]
    end

    subgraph Storage["Storage and Indexing"]
        Metadata["PostgreSQL / SQLite Metadata"]
        Objects["LocalObjectStorage"]
        Vector["Document and Chunk Vector Index"]
        Qdrant["Qdrant Vector Database"]
    end

    subgraph Interface["Serving Layer"]
        API["FastAPI Backend"]
        Search["Search API"]
        Docs["Document Retrieval API"]
        Dashboard["Streamlit Dashboard"]
        Answers["Cited Analysis API"]
    end

    Sources --> Orchestration
    Orchestration --> Pipeline
    Pipeline --> Quality
    Quality --> Processing
    Processing --> Metadata
    Processing --> Objects
    Processing --> Vector
    Vector --> Qdrant
    Vector --> Analysis
    Metadata --> Analysis
    Metadata --> Reporting
    Metadata --> API
    Vector --> Search
    Metadata --> Docs
    Analysis --> Answers
    Dashboard --> API
```

## Data Flow

```mermaid
sequenceDiagram
    participant Scheduler as Scheduler / Airflow / CLI
    participant Manifest as Source Manifest
    participant Quality as Data Quality
    participant Reader as Document Reader
    participant Processor as Processing Layer
    participant Store as Metadata/Object/Vector Stores
    participant Metrics as Metrics and Error Reports

    Scheduler->>Manifest: Load document sources
    Manifest->>Quality: Validate URI, source type and metadata
    Quality->>Quality: Detect duplicate sources
    Quality->>Reader: Read local, URL or PDF document
    Reader->>Quality: Validate extracted text
    Quality->>Processor: Clean, classify, summarise and extract keywords
    Processor->>Store: Persist metadata, raw text and search index
    Processor->>Metrics: Record document count, skips, duration and errors
```

## Repository Structure

```text
fkip/
  domain/                 Domain models, financial processing and quality rules
  application/            Pipeline orchestration, RAG analysis, metrics, reporting and benchmarks
  infrastructure/         Document readers, embeddings, repositories, object storage and vector search
  interfaces/api/         FastAPI HTTP interface
  interfaces/dashboard/   Streamlit dashboard client and UI
  bootstrap.py            Dependency wiring
  cli.py                  Command-line entry point
dags/                     Airflow-compatible scheduled ingestion DAG
infra/postgres/schema.sql PostgreSQL metadata schema
samples/                  Sample financial source manifest and documents
tests/                    Unit tests for processing, quality, pipeline and search
Dockerfile                API container
docker-compose.yml        API, dashboard, PostgreSQL, MinIO and Qdrant services
```

## Engineering Features

- Clean architecture with explicit domain/application/infrastructure boundaries
- FastAPI backend for ingestion, retrieval and search
- Streamlit dashboard connected to the FastAPI layer
- Retrieval-augmented financial analysis with chunk citations
- CLI for ingestion, scheduled execution, report generation and benchmarking
- Airflow-compatible DAG structure in `dags/`
- Data validation for source metadata and extracted document text
- Duplicate detection at manifest level
- Run-level processing statistics and error reporting
- JSON structured logging for container and pipeline observability
- SQLite local metadata adapter and PostgreSQL deployment adapter
- LocalObjectStorage for raw extracted document text, with an object storage abstraction in place
- Local vector store for tests and Qdrant vector store for production-style retrieval
- Deterministic local embedding pipeline with optional OpenAI summarisation
- Docker Compose stack with PostgreSQL and Qdrant wired through configuration
- MinIO included in Docker Compose as a future production deployment option; it is not the active storage adapter yet
- Standard-library test suite

## Data Quality Layer

The pipeline validates each source before processing:

- URI must be present and valid.
- Local files must exist before ingestion starts.
- Publication dates must use `YYYY-MM-DD`.
- Titles must be meaningful when provided.
- Extracted text must pass a minimum length threshold.
- Duplicate manifest entries are skipped and counted.

Each run produces a `PipelineRunResult` with:

- `sources_seen`
- `documents_ingested`
- `documents_skipped`
- `duplicate_sources`
- `validation_failures`
- `errors`
- `duration_seconds`
- `document_ids`

## Observability

Application logs are emitted as JSON with timestamps, log level, logger name, message and structured context. Pipeline runs write metrics to `data/metrics/` by default.

Example:

```bash
python -m fkip.cli ingest samples/financial_sources.json \
  --metrics-output data/metrics/latest_ingestion.json
```

Scheduled ingestion also records the latest run:

```bash
python -m fkip.cli schedule samples/financial_sources.json \
  --interval-seconds 86400 \
  --max-runs 1 \
  --metrics-output data/metrics/latest_scheduled_ingestion.json
```

## Orchestration

The platform supports three orchestration modes:

- **CLI batch ingestion** for local and CI execution.
- **Scheduled runner** for simple cron-style deployment.
- **Airflow DAG** in `dags/financial_knowledge_ingestion_dag.py` for production workflow managers.

The Airflow DAG is intentionally thin: it delegates business logic to `fkip.application.pipeline` so orchestration does not duplicate pipeline behaviour.

## Vector Storage

The project supports two vector storage backends:

| Backend | Use case | Configuration |
| --- | --- | --- |
| `local` | Unit tests and lightweight local demos | `VECTOR_STORE_BACKEND=local` |
| `qdrant` | Production-style Docker path and scalable retrieval | `VECTOR_STORE_BACKEND=qdrant` |

The local adapter stores document and chunk vectors in a JSON file. The Qdrant adapter stores document-level vectors and chunk-level vectors in separate Qdrant collections and is selected in `.env.docker.example`.

Qdrant configuration:

```bash
export VECTOR_STORE_BACKEND=qdrant
export QDRANT_URL=http://localhost:6333
export QDRANT_DOCUMENT_COLLECTION=fkip_documents
export QDRANT_CHUNK_COLLECTION=fkip_document_chunks
export EMBEDDING_DIMENSIONS=256
```

Run the Qdrant integration test after starting Qdrant:

```bash
docker compose up -d qdrant
QDRANT_INTEGRATION_URL=http://localhost:6333 \
  python -m unittest tests.test_qdrant_vector_store_integration
```

The adapter uses Qdrant's REST API to create collections, upsert points and search document/chunk vectors.

## Quick Start

For a complete copy-pasteable walkthrough with expected terminal output, see [DEMO.md](DEMO.md).

For the realistic 500+ public financial document dataset pipeline, see [docs/DATASET.md](docs/DATASET.md).

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ingest the sample financial sources

```bash
python -m fkip.cli ingest samples/financial_sources.json
```

### 3. Search the indexed knowledge base

```bash
python -m fkip.cli search "operational resilience fca"
```

### 4. Generate an intelligence digest

```bash
python -m fkip.cli report --output Research_Digest.md
```

### 5. Ask a cited financial analysis question

```bash
python -m fkip.cli answer "What does the FCA say about operational resilience?" --limit 3
```

The answer is generated from retrieved document chunks and returns citations with document ID, title, issuer, source URI, chunk ID and relevance score.

### 6. Rebuild embeddings for existing documents

```bash
python -m fkip.cli reindex
```

Use this after changing chunking or embedding settings, or when upgrading an older document index.

### 7. Benchmark ingestion performance

```bash
python -m fkip.cli benchmark samples/financial_sources.json \
  --iterations 5 \
  --output data/metrics/benchmark.json
```

### 8. Start the Web Research Workspace (Production Mode)

The FastAPI server automatically serves the compiled React 19 + TypeScript frontend application:

```bash
uvicorn fkip.interfaces.api.main:app --host 0.0.0.0 --port 8000
```

Open:
- **Web Research Workspace**: `http://localhost:8000`
- API Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Overview Statistics: `http://localhost:8000/overview`

### 9. Frontend Development Mode (Hot Reload)

For frontend UI development with Vite HMR:

```bash
# Terminal 1: authoritative backend
uvicorn fkip.interfaces.api.main:app --port 8000 --reload

# Terminal 2: Vite development server with proxy
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies API calls directly to `http://localhost:8000`.

### 10. Start the Operational Streamlit Dashboard (Diagnostic Use)

The original Streamlit interface remains fully supported for diagnostic and operational telemetry:

```bash
streamlit run fkip/interfaces/dashboard/app.py
```

Open `http://localhost:8501`.

## Authoritative API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serves compiled React 19 Web Research Workspace |
| `GET` | `/health` | Service health and environment status |
| `GET` | `/overview` | Workspace overview statistics (issuers, documents, year/type distributions) |
| `GET` | `/documents` | List or paginate documents with search, issuer, type, and year filters |
| `GET` | `/documents/{document_id}` | Retrieve document summary, full clean text, and metadata |
| `GET` | `/documents/{document_id}/chunks` | Retrieve chunked vector passages for a specific document |
| `POST` | `/documents` | Ingest one document from a validated URI (with SSRF protection) |
| `GET` | `/search?q=...` | Semantic vector search across indexed documents |
| `GET` | `/pipeline-stats` | Latest ingestion metrics and execution errors |
| `GET` | `/pipeline-runs` | Historical run ledger persisted in metadata store |
| `POST` | `/analysis/answer` | Traceable RAG question answering with chunk-level citations |
| `POST` | `/analysis/compare` | Isolated side-by-side disclosure comparison between two issuers |


Example analysis request:

```json
{
  "question": "What does the FCA say about operational resilience?",
  "limit": 3
}
```

Expected response shape:

```json
{
  "question": "What does the FCA say about operational resilience?",
  "answer": "Based on the retrieved financial document evidence: ... [1]",
  "retrieval_count": 3,
  "citations": [
    {
      "document_id": "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6",
      "title": "FCA Operational Resilience Excerpt",
      "issuer": "Financial Conduct Authority",
      "uri": "samples/fca_operational_resilience_excerpt.txt",
      "chunk_id": "f01a4ae1-8a4e-55b2-b0d7-d08030bb81f6:0",
      "chunk_index": 0,
      "score": 0.1943,
      "excerpt": "The FCA expects firms to identify important business services..."
    }
  ]
}
```

## Retrieval-Augmented Analysis

![Retrieval-Augmented Analysis Flow](docs/images/rag_retrieval_flow.svg)

The RAG layer is designed for financial document analysis, not general chat.

Pipeline:

```text
Processed document -> overlapping chunks -> deterministic embeddings -> vector index
Question -> query embedding -> top chunk retrieval -> cited financial answer
```

Design decisions:

- Chunking is implemented in `fkip.domain.chunking`.
- Embedding generation is implemented in `fkip.infrastructure.embeddings`.
- Retrieval and answer construction live in `fkip.application.analysis`.
- FastAPI only exposes the service through `/analysis/answer`.
- The default answer mode is extractive and deterministic.
- Optional OpenAI summarisation is available by setting `LLM_PROVIDER=openai`.
- Existing documents can be re-embedded with `python -m fkip.cli reindex`.

Optional LLM configuration:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL=gpt-5-mini
```

When using the optional LLM provider, the prompt instructs the model to use only retrieved evidence and include bracketed citations.

## Streamlit Dashboard Demo

Before opening the dashboard, create sample data and metrics:

```bash
python -m fkip.cli ingest samples/financial_sources.json \
  --metrics-output data/metrics/latest_ingestion.json
uvicorn fkip.interfaces.api.main:app --reload
streamlit run fkip/interfaces/dashboard/app.py
```

Expected dashboard screens:

```text
Pipeline Statistics
Sources Seen: 3 | Ingested: 3 | Skipped: 0 | Duplicates: 0 | Duration (s): ~0.003
Status: No pipeline errors reported in the latest metrics file.
```

```text
Document Search
Query: operational resilience fca

Result 1: FCA Operational Resilience Excerpt
Score: ~0.165
Issuer: Financial Conduct Authority
Source type: fca_regulatory
Topics: Risk & Compliance, Technology & Operations, ESG & Sustainability
Source URI: samples/fca_operational_resilience_excerpt.txt
```

```text
Financial Analysis
Question: What does the FCA say about operational resilience?
Answer: Based on the retrieved financial document evidence: ... [1]
Citations: FCA Operational Resilience Excerpt, Barclays Annual Report Excerpt
```

```text
Document Catalog
Indexed Documents: 3
Source Types: 3
Rows: Barclays Annual Report Excerpt, FCA Operational Resilience Excerpt, UK Market News Excerpt
```

To capture screenshots for a portfolio README, use:

```bash
mkdir -p docs/screenshots
# macOS example after opening http://localhost:8501:
screencapture -i docs/screenshots/streamlit_dashboard.png
```

## Docker Deployment

![Docker Compose Service Interaction](docs/images/deployment_services.svg)

```bash
docker compose up --build
```

The Compose stack includes:

- API service
- Streamlit dashboard
- Alembic migration service
- PostgreSQL service using the `pgvector/pgvector` image
- MinIO as a future object-storage-compatible deployment option
- Qdrant for document and chunk vector retrieval

The current application code writes raw extracted document text through `LocalObjectStorage`, configured by `OBJECT_STORE_PATH`. MinIO is present in Docker Compose to show the intended production-style storage boundary, but an S3/MinIO adapter is not yet wired as the active storage implementation.

PostgreSQL is used for structured metadata and ingestion lineage. Vector retrieval is handled by Qdrant rather than PostgreSQL vector columns.

## PostgreSQL Migrations

Alembic owns the production PostgreSQL schema. Runtime table creation is intentionally not used by the PostgreSQL adapter.

Run migrations locally:

```bash
export DATABASE_URL=postgresql://fkip:fkip@localhost:5432/financial_intelligence
alembic upgrade head
```

Create a new migration after changing the persistence model:

```bash
alembic revision -m "describe schema change"
```

Docker Compose runs migrations through the one-shot `migrate` service before the API starts:

```bash
docker compose up migrate
docker compose up --build
```

Run PostgreSQL integration tests against a local database:

```bash
POSTGRES_INTEGRATION_DATABASE_URL=postgresql://fkip:fkip@localhost:5432/financial_intelligence \
  python -m unittest tests.test_postgres_persistence_integration
```

## Continuous Integration

GitHub Actions runs a lightweight CI workflow from `.github/workflows/ci.yml` on pushes, pull requests and manual dispatch.

Automated checks:

- Install Python dependencies from `requirements.txt`
- Run the standard-library unit test suite
- Compile Python modules with `compileall`
- Validate Docker Compose configuration
- Build the Docker image
- Validate Alembic migration SQL generation

The default CI path does not require live PostgreSQL or Qdrant services. Integration tests are included in the repository but skipped unless their environment variables are provided:

```bash
POSTGRES_INTEGRATION_DATABASE_URL=postgresql://fkip:fkip@localhost:5432/financial_intelligence \
  python -m unittest tests.test_postgres_persistence_integration

QDRANT_INTEGRATION_URL=http://localhost:6333 \
  python -m unittest tests.test_qdrant_vector_store_integration
```

This keeps CI fast for portfolio review while still documenting how production dependencies are verified.

## Engineering Decisions

- **Keep AI minimal and useful**: retrieval and summarisation are implemented as deterministic pipeline steps rather than adding unnecessary agent features.
- **Use clean architecture**: domain logic is isolated from FastAPI, storage and orchestration concerns.
- **Make ingestion idempotent**: document IDs are derived from source URIs so repeated ingestion updates the same logical document.
- **Validate early**: source and metadata issues are caught before expensive processing.
- **Record failed work**: validation and ingestion failures are returned in run metrics rather than disappearing into logs.
- **Keep local development simple**: SQLite and local file adapters make the project easy to run without cloud services.
- **Design for production swap-outs**: storage and vector search are behind interfaces; the current Docker path uses Qdrant while local tests use the lightweight JSON adapter.

## Scalability Considerations

The current implementation is designed to evolve from tens of documents to hundreds or thousands:

- Manifest-level duplicate detection avoids unnecessary repeated work.
- Deterministic IDs make batch reprocessing idempotent.
- Quality gates prevent invalid data from polluting downstream stores.
- Metrics capture throughput and failure rates for capacity planning.
- Benchmarking gives a baseline for documents-per-second on local hardware.
- Storage adapters separate metadata, raw documents and retrieval indexes.
- Airflow compatibility enables retries, scheduling, backfills and task monitoring.

Recommended production upgrades for larger workloads:

- Move `LocalObjectStorage` to an S3/MinIO adapter.
- Add payload indexes and operational snapshots for Qdrant collections.
- Add queue-based ingestion workers for parallel processing.
- Add integration tests against PostgreSQL in CI.
- Add OpenTelemetry tracing and Prometheus metrics.

## Testing & Verification

The platform maintains a comprehensive multi-tier test suite covering core domain algorithms, pipeline orchestration, API contracts, SSRF security validation, and automated browser end-to-end flows.

### 1. Standard Unit & Integration Test Suite

```bash
python -m unittest discover -s tests
```

Current verified result:
```text
Ran 34 tests in 0.265s

OK (skipped=7)
```

Test coverage includes:
- **API Extensions**: Pagination, multi-parameter filtering, document chunks, SSRF attack rejection, issuer-isolated search.
- **Financial Processing**: Topic classification, keyword extraction, sentence-level deterministic extractive summarisation.
- **Validation & Quality**: Metadata validation, source URI validation, duplicate detection, and pipeline failure accounting.
- **RAG & Chunking**: Chunk size bounds, overlap consistency, vector search ranking, and citation grounding.

### 2. Browser End-to-End Tests (Playwright)

To verify the live user experience across all 5 workspace views using headless Chrome:

```bash
RUN_BROWSER_TESTS=1 python -m unittest tests/test_browser_e2e.py
```

Current verified result:
```text
.....
----------------------------------------------------------------------
Ran 5 tests in 6.755s

OK
```

### 3. Automated Screenshot Capture

To regenerate the high-resolution documentation screenshots under `docs/images/`:

```bash
python scripts/capture_e2e_screenshots.py
```

## Reproducible Demo Dataset Ground Truth

| Metric | Verified Ground Truth Value |
| --- | --- |
| **Total Ingested Documents** | 15 documents (12 official SEC filings + 3 regulatory/market excerpts) |
| **Unique Issuers** | 7 (`AMAZON COM INC`, `Alphabet Inc.`, `Apple Inc.`, `Microsoft Corporation`, `Barclays PLC`, `Financial Conduct Authority`, `UK Market News`) |
| **Indexed Vector Chunks** | 2,078 chunks |
| **Publication Years** | 2025, 2026 |
| **Raw Content Size** | 38.18 MB (HTML and text) |
| **Metadata Store** | SQLite (`data/metadata.db`) & PostgreSQL schema |
| **Vector Index** | LocalVectorStore (`data/index/vector_index.json`) & Qdrant |

> [!NOTE]
> The original repository's 500+ document figure is a planned pipeline scale target for long-running ingestion. The authentic, reproducible offline demo dataset in this repository contains 15 verified, multi-megabyte SEC filings and regulatory publications providing 2,078 vector chunks.


## Portfolio Relevance

This project demonstrates skills relevant to UK software, data and platform engineering roles:

- Backend Engineering: FastAPI, API design, repository pattern
- Data Engineering: ingestion, validation, ETL, quality gates and benchmarking
- Cloud Engineering: Docker, service composition and storage separation
- AI Engineering: retrieval-oriented indexing and document intelligence
- Production Engineering: logging, metrics, error reporting, orchestration and maintainable architecture
