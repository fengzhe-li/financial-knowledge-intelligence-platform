-- Reference schema for the PostgreSQL production persistence layer.
-- Alembic is the source of truth for applying this schema:
--   alembic upgrade head

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    issuer TEXT,
    published_at DATE,
    uri TEXT NOT NULL,
    object_key TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    topics JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_issuer ON documents(issuer);
CREATE INDEX IF NOT EXISTS idx_documents_topics ON documents USING GIN(topics);
CREATE INDEX IF NOT EXISTS idx_documents_published_at ON documents(published_at);

CREATE TABLE IF NOT EXISTS document_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    uri TEXT NOT NULL,
    source_type TEXT NOT NULL,
    issuer TEXT,
    published_at DATE,
    title TEXT,
    content_hash TEXT,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_document_sources_document_uri UNIQUE (document_id, uri)
);

CREATE INDEX IF NOT EXISTS idx_document_sources_document_id ON document_sources(document_id);
CREATE INDEX IF NOT EXISTS idx_document_sources_uri ON document_sources(uri);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    manifest_path TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    sources_seen INTEGER NOT NULL DEFAULT 0,
    documents_ingested INTEGER NOT NULL DEFAULT 0,
    documents_skipped INTEGER NOT NULL DEFAULT 0,
    duplicate_sources INTEGER NOT NULL DEFAULT 0,
    validation_failures INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_started_at ON ingestion_runs(started_at);

CREATE TABLE IF NOT EXISTS ingestion_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT NOT NULL REFERENCES ingestion_runs(run_id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    source_uri TEXT NOT NULL,
    status TEXT NOT NULL,
    stage TEXT,
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ingestion_items_run_id ON ingestion_items(run_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_items_status ON ingestion_items(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_items_document_id ON ingestion_items(document_id);
