# Interview Notes

These notes are designed for UK FinTech Backend Engineer and Data Engineer interviews. They describe the implemented system honestly and highlight the engineering trade-offs behind it.

## What Problem The Platform Solves

Financial firms consume large volumes of semi-structured documents: annual reports, regulatory publications, market news, public filings and operational risk material. The platform provides a production-style pipeline for collecting those documents, validating them, extracting text, storing metadata, indexing content and retrieving cited evidence for financial analysis.

The core value is not a chatbot. The core value is a reliable data pipeline and retrieval layer for financial knowledge.

## Current Implemented Architecture

The implementation is split into clean layers:

- Domain: source models, processed document models, validation, chunking and financial text processing.
- Application: ingestion pipeline, scheduled orchestration, metrics, benchmarking, reporting, indexing and RAG analysis.
- Infrastructure: document reading, metadata repositories, local object storage, embedding generation, local vector search and Qdrant vector search.
- Interfaces: FastAPI backend, Streamlit dashboard and CLI commands.

The current Docker path wires PostgreSQL, Qdrant, FastAPI and Streamlit. Raw extracted text is stored through `LocalObjectStorage`; MinIO is present in Docker Compose as a future object-storage-compatible deployment option.

## Why PostgreSQL And Qdrant Are Separated

PostgreSQL stores structured metadata and lineage: document IDs, titles, issuers, source types, publication dates, ingestion runs and ingestion items. This data needs transactional consistency, relational constraints and auditability.

Qdrant stores dense vectors for semantic retrieval over documents and chunks. This workload needs nearest-neighbour search and vector-specific indexing rather than relational joins.

Separating them keeps each storage system focused: PostgreSQL is the source of truth for metadata, while Qdrant is the retrieval index.

## Why LocalVectorStore Is Retained Alongside Qdrant

`LocalVectorStore` keeps unit tests and demos fast, deterministic and dependency-light. It avoids requiring a running Qdrant service for every local test run.

Qdrant is used for the production-style path, where retrieval needs a dedicated vector database. Both stores implement the same interface, so the application layer does not know which backend is active.

## How The Ingestion Pipeline Works

The pipeline loads a JSON manifest of document sources, validates each source, skips duplicate URIs, reads local or remote document text, validates extracted content, processes the document, stores metadata, writes raw text and updates the vector index.

For batch runs, the pipeline records run-level metrics: sources seen, documents ingested, skipped documents, duplicate sources, validation failures, errors, duration and document IDs. In PostgreSQL mode it can also persist ingestion runs and ingestion items for lineage.

## Data Quality And Lineage Strategy

Quality checks happen before expensive processing:

- Source URI is required and validated.
- Local files must exist.
- Publication dates must use ISO format.
- Titles and issuers must meet basic quality thresholds.
- Extracted text must meet a minimum length.
- Duplicate manifest entries are skipped and counted.

Lineage is represented through deterministic document IDs derived from source URIs, source metadata, ingestion run records and ingestion item records. This makes repeated ingestion idempotent and gives enough audit context to explain where each document came from.

## Why Deterministic Extractive Answers Are The Default

The default answer mode is deterministic because financial document analysis needs traceability more than creativity. The extractive summariser returns evidence from retrieved chunks with citations, which reduces hallucination risk and makes outputs easier to validate.

This is a deliberate FinTech design choice: cite the source first, then summarise.

## How Optional LLM Summarisation Fits Into The RAG Layer

Optional OpenAI summarisation is available behind `LLM_PROVIDER=openai`. It is not exposed as a generic chatbot. The LLM receives only retrieved evidence and is instructed to answer with bracketed citations.

The retrieval service, citation construction and API contract remain the same whether the summariser is deterministic or LLM-backed.

## Main Architecture Trade-Offs

- Synchronous ingestion keeps the project simple and demo-friendly, but long-running ingestion should become job-based in production.
- Local object storage is easy to run and test, but production document storage should use S3 or MinIO.
- Hash-based deterministic embeddings make tests stable, but production retrieval quality would improve with a finance-appropriate embedding model.
- Docker Compose is enough to demonstrate service boundaries, but managed production deployment would need secrets, networking, backups and monitoring.
- The Airflow DAG is intentionally thin, which avoids duplicated business logic but keeps orchestration examples compact.

## Current Scalability Limitations

- API ingestion processes documents synchronously.
- There is no queue-backed worker pool.
- Document-level retry and resume behavior is basic.
- Local object storage is not suitable for distributed workers.
- PostgreSQL connections are opened per repository operation rather than pooled.
- Qdrant payload indexing, snapshots and backup strategy are not yet configured.
- Observability is structured logging plus metrics files, not a full tracing/metrics stack.

## Scaling From Hundreds To Thousands Or Millions Of Filings

For hundreds of filings, the current batch pipeline, PostgreSQL adapter and Qdrant adapter are enough to demonstrate the design.

For thousands of filings, I would add:

- Queue-backed ingestion workers.
- Document checksums and source artifact immutability.
- S3/MinIO object storage adapter.
- PostgreSQL connection pooling and indexes tuned from query patterns.
- Qdrant payload indexes, snapshots and collection lifecycle management.
- Retry policies with checkpointed processing stages.

For millions of filings, I would add:

- Partitioned ingestion workloads by source, issuer, date or filing type.
- Backfill orchestration with Airflow or a managed workflow engine.
- Separate services for collection, extraction, indexing and serving.
- Batch embedding jobs with rate limits and cost controls.
- Data retention, reprocessing and schema evolution policies.

## What I Would Improve Next In A Real Production Environment

- Replace synchronous API ingestion with job submission and worker processing.
- Wire a real S3/MinIO object storage adapter.
- Add PostgreSQL pooling and stronger transaction management.
- Add retry, backoff and resume at document-processing stage level.
- Add OpenTelemetry, Prometheus metrics and alerting.
- Run PostgreSQL and Qdrant integration tests in CI service containers.
- Add authentication and role-based access if the API served non-public data.

## Why I Did Not Add Spark, Kafka Or Kubernetes

I intentionally avoided Spark, Kafka and Kubernetes because they would add operational surface area without improving the portfolio signal for this project.

The main engineering problem is document ingestion, validation, metadata persistence, indexing and retrieval. Docker Compose, FastAPI, PostgreSQL, Qdrant, Alembic and Airflow-compatible orchestration demonstrate the relevant backend and data engineering skills without pretending this is a high-throughput streaming or distributed compute system.

## 60-Second Interview Explanation

This project is a production-style FinTech data platform for financial documents. It ingests manifests or collected SEC filings, validates metadata and extracted text, deduplicates sources, stores metadata in SQLite or PostgreSQL, writes raw text through a storage abstraction and indexes document chunks for retrieval using either a local vector store or Qdrant. The FastAPI layer exposes document search, retrieval, pipeline metrics and cited financial analysis, while Streamlit provides a demo dashboard. I focused on engineering quality: clean architecture, Alembic migrations, structured logging, processing metrics, CI checks and clear separation between metadata storage and vector retrieval.

## 2-Minute Interview Explanation

The platform started as a small document digest prototype and was redesigned into a production-style financial knowledge system. The core workflow is ingestion, validation, processing, persistence, indexing and retrieval.

The domain layer owns document models, quality checks, chunking and financial text processing. The application layer owns the ingestion pipeline, metrics, reporting, benchmarking and RAG analysis. Infrastructure adapters handle document reading, SQLite or PostgreSQL metadata storage, local object storage and local or Qdrant vector retrieval. Interfaces are kept thin: FastAPI calls application services, Streamlit calls FastAPI and the CLI runs repeatable batch workflows.

For data engineering, the pipeline tracks duplicates, validation failures, skipped documents, errors, duration and document IDs. PostgreSQL migrations define documents, document sources, ingestion runs and ingestion items. For retrieval, the system chunks documents, embeds content deterministically by default and returns cited answers grounded in retrieved chunks. Optional LLM summarisation is available, but it is deliberately not a generic chatbot.

The main trade-off is that the project is production-style rather than fully production-operated. For a real deployment I would add queue-backed workers, S3 or MinIO storage, connection pooling, stronger retry/resume behavior and full observability. I avoided Spark, Kafka and Kubernetes because they would be disproportionate for this document pipeline and would distract from the backend/data engineering fundamentals.

## Likely Technical Interview Questions

1. Why separate PostgreSQL and Qdrant?

PostgreSQL is the system of record for structured metadata, lineage and ingestion state. Qdrant is an optimized retrieval index for vector similarity search. Keeping them separate avoids forcing relational storage to solve vector search or treating the vector database as an audit database.

2. How is ingestion idempotent?

Document IDs are derived deterministically from source URIs. Re-ingesting the same source updates the same logical document, and manifest-level duplicate detection prevents duplicate work within a batch.

3. What happens when a document fails validation?

The pipeline skips the document, records a validation failure, adds a structured error to the run result and persists an ingestion item in PostgreSQL mode. The failure is visible in metrics rather than disappearing into logs.

4. Why is the default answer mode extractive?

Financial analysis needs traceability. Extractive answers cite retrieved chunks directly, which is easier to validate and safer than generating unsupported claims. LLM summarisation is optional and constrained to retrieved evidence.

5. How would you scale ingestion?

I would turn ingestion into asynchronous jobs, add queue-backed workers, store raw source artifacts in S3 or MinIO, checkpoint each processing stage and use Airflow for backfills and scheduled collection.

6. Why keep LocalVectorStore if Qdrant exists?

It keeps tests deterministic and fast without requiring infrastructure. The same interface lets the application switch to Qdrant through configuration for the production-style path.

7. What are the main reliability gaps?

The biggest gaps are synchronous API ingestion, limited retry/resume behavior, local object storage and lack of connection pooling. These are documented as target production improvements rather than hidden.

8. What does this project show for a FinTech backend role?

It shows API design, storage separation, migrations, data quality, lineage, retrieval grounding, Dockerized services, CI checks and pragmatic engineering trade-offs around reliability and scalability.
