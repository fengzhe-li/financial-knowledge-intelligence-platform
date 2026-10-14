import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { PipelineRun, PipelineStatsResponse } from '../types/api';
import {
  Activity,
  AlertTriangle,
  Clock,
  Database,
  FileText,
  Layers,
  RefreshCw,
  Terminal,
  Server,
  Lock,
} from 'lucide-react';

export const PipelineOperationsView: React.FC = () => {
  const [stats, setStats] = useState<PipelineStatsResponse | null>(null);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOpsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, runsRes] = await Promise.all([
        api.getPipelineStats(),
        api.getPipelineRuns(10),
      ]);
      setStats(statsRes);
      setRuns(runsRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pipeline telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpsData();
  }, []);

  const latest = stats?.metrics;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Activity size={18} color="var(--accent-cyan)" /> Pipeline Operations & Ingestion Observability
            </div>
            <div className="card-subtitle">
              Audit run-level metrics, processing duration, data quality checks, and lineage storage records.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              className="btn btn-secondary"
              onClick={fetchOpsData}
              disabled={loading}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
            >
              <RefreshCw size={14} className={loading ? 'spinner' : ''} /> Refresh Telemetry
            </button>
          </div>
        </div>

        {/* Read-Only Governance Notice */}
        <div
          style={{
            background: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
          }}
        >
          <Lock size={16} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
          <div>
            <strong>Read-Only Governance Enforced:</strong> Unrestricted ingestion, remote arbitrary URL fetching, and vector index re-computation are restricted to authenticated backend CLI runners and scheduled DAGs to eliminate SSRF and denial-of-service risks.
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-rose)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-rose)', fontWeight: 600 }}>
            <AlertTriangle size={16} /> Telemetry Error
          </div>
          <p style={{ marginTop: '0.4rem', color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      )}

      {/* Latest Metrics Snapshot Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Clock size={16} /> Latest Ingestion Run Snapshot
          </div>
          {latest && (
            <span
              className="badge"
              style={{
                background: (latest.errors?.length || 0) > 0 ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                color: (latest.errors?.length || 0) > 0 ? '#fb7185' : '#34d399',
              }}
            >
              {(latest.errors?.length || 0) > 0 ? 'Completed with errors' : 'Healthy execution'}
            </span>
          )}
        </div>

        {latest ? (
          <div>
            <div className="metrics-grid" style={{ marginBottom: '1rem' }}>
              <div className="metric-card">
                <div className="metric-label">Sources Seen</div>
                <div className="metric-value">{latest.sources_seen}</div>
                <div className="metric-sub">From manifest input</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Ingested Documents</div>
                <div className="metric-value" style={{ color: 'var(--accent-emerald)' }}>
                  {latest.documents_ingested}
                </div>
                <div className="metric-sub">Valid and indexed</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Skipped Sources</div>
                <div className="metric-value">{latest.documents_skipped}</div>
                <div className="metric-sub">Duplicates & invalid</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Processing Duration</div>
                <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
                  {latest.duration_seconds}s
                </div>
                <div className="metric-sub">Wall clock time</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)', background: 'var(--bg-input)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <strong>Run ID:</strong> <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{latest.run_id}</code>
              </div>
              <div>
                <strong>Started At:</strong> {latest.started_at ? new Date(latest.started_at).toLocaleString() : '—'}
              </div>
              <div>
                <strong>Finished At:</strong> {latest.finished_at ? new Date(latest.finished_at).toLocaleString() : '—'}
              </div>
              <div>
                <strong>Metrics Artifact:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>{stats?.metrics_path}</code>
              </div>
              <div>
                <strong>Validation Failures:</strong> {latest.validation_failures}
              </div>
              <div>
                <strong>Duplicate Sources Skipped:</strong> {latest.duplicate_sources}
              </div>
            </div>

            {/* Error Details if any */}
            {latest.errors && latest.errors.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-rose)', marginBottom: '0.4rem' }}>
                  Execution Errors ({latest.errors.length})
                </div>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Source URI</th>
                        <th>Stage</th>
                        <th>Error Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {latest.errors.map((err, i) => (
                        <tr key={i}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{err.source_uri}</td>
                          <td><span className="badge badge-source-fca">{err.stage}</span></td>
                          <td style={{ color: 'var(--accent-rose)' }}>{err.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {stats?.message || 'No latest ingestion metrics snapshot found.'}
          </div>
        )}
      </div>

      {/* Historical Pipeline Runs (Persisted in SQLite / Postgres) */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Database size={16} /> Historical Run Records
            </div>
            <div className="card-subtitle">
              Persisted run ledger stored in <code>ingestion_runs</code> table.
            </div>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {runs.length} run{runs.length === 1 ? '' : 's'} recorded
          </span>
        </div>

        {runs.length === 0 ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No historical run records found in metadata store. Run ingestion with the updated repository layer to log future executions.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID & Manifest</th>
                  <th>Status</th>
                  <th>Seen</th>
                  <th>Ingested</th>
                  <th>Skipped</th>
                  <th>Duration</th>
                  <th>Started At</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.775rem' }}>
                        {run.run_id.slice(0, 38)}...
                      </div>
                      {run.manifest_path && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Manifest: {run.manifest_path}
                        </div>
                      )}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background:
                            run.status === 'completed'
                              ? 'rgba(16, 185, 129, 0.15)'
                              : run.status === 'completed_with_errors'
                              ? 'rgba(244, 63, 94, 0.15)'
                              : 'rgba(56, 189, 248, 0.15)',
                          color:
                            run.status === 'completed'
                              ? '#34d399'
                              : run.status === 'completed_with_errors'
                              ? '#fb7185'
                              : '#38bdf8',
                        }}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{run.sources_seen}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      {run.documents_ingested}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {run.documents_skipped}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{run.duration_seconds}s</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Storage Architecture & Lineage Info */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Server size={16} /> Storage Tier & Lineage Architecture
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              <Database size={15} color="var(--accent-blue)" /> Metadata Repository
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Stores document metadata, publication dates, topics, keywords, and ingestion run telemetry.
            </p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              Engine: SQLite (Local) / PostgreSQL 16 (Docker)
            </div>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              <FileText size={15} color="var(--accent-emerald)" /> Raw Object Storage
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Preserves unmodified clean source text extracted from HTML filings and PDFs, keyed by deterministic document UUID.
            </p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              Path: <code>data/documents/</code> (LocalObjectStorage)
            </div>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              <Layers size={15} color="var(--accent-cyan)" /> Vector Store Index
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Embeds 120-word chunk sliding windows with Blake2b hashing (256-dim L2 normalized) for cosine similarity search.
            </p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              Backend: Local JSON Index / Qdrant v1.12.5
            </div>
          </div>
        </div>

        {/* Reproducible CLI Commands Guide */}
        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <Terminal size={14} /> Reproducible Batch Ingestion Commands
          </div>
          <pre
            style={{
              background: 'var(--bg-input)',
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-highlight)',
              overflowX: 'auto',
            }}
          >
            # Ingest demo dataset and update metrics:&#10;python3 -m fkip.cli ingest data/manifests/demo_financial_documents.json --metrics-output data/metrics/latest_ingestion.json&#10;&#10;# Rebuild vector index from metadata store:&#10;python3 -m fkip.cli reindex
          </pre>
        </div>
      </div>
    </div>
  );
};
