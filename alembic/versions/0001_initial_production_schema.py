"""Initial production persistence schema.

Revision ID: 0001_initial_production_schema
Revises: None
Create Date: 2026-08-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_production_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "documents",
        sa.Column("document_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("clean_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_documents_source_type", "documents", ["source_type"])
    op.create_index("idx_documents_issuer", "documents", ["issuer"])
    op.create_index("idx_documents_topics", "documents", ["topics"], postgresql_using="gin")
    op.create_index("idx_documents_published_at", "documents", ["published_at"])

    op.create_table(
        "document_sources",
        sa.Column("source_id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_document_sources_document_id", "document_sources", ["document_id"])
    op.create_index("idx_document_sources_uri", "document_sources", ["uri"])
    op.create_unique_constraint("uq_document_sources_document_uri", "document_sources", ["document_id", "uri"])

    op.create_table(
        "ingestion_runs",
        sa.Column("run_id", sa.Text(), primary_key=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("manifest_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("sources_seen", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("documents_ingested", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("documents_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duplicate_sources", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("validation_failures", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index("idx_ingestion_runs_started_at", "ingestion_runs", ["started_at"])

    op.create_table(
        "ingestion_items",
        sa.Column("item_id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("ingestion_runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_ingestion_items_run_id", "ingestion_items", ["run_id"])
    op.create_index("idx_ingestion_items_status", "ingestion_items", ["status"])
    op.create_index("idx_ingestion_items_document_id", "ingestion_items", ["document_id"])


def downgrade() -> None:
    op.drop_table("ingestion_items")
    op.drop_table("ingestion_runs")
    op.drop_table("document_sources")
    op.drop_table("documents")
