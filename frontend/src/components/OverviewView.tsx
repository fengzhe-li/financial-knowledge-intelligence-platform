import React from 'react';
import type { OverviewStats } from '../types/api';
import type { NavTab } from './Header';
import {
  FileText,
  Building2,
  Calendar,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
} from 'lucide-react';

interface OverviewViewProps {
  stats: OverviewStats | null;
  loading: boolean;
  error: string | null;
  onNavigate: (tab: NavTab) => void;
  onSelectDocument: (docId: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  stats,
  loading,
  error,
  onNavigate,
  onSelectDocument,
}) => {
  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', gap: '1rem' }}>
        <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px' }} />
        <div style={{ color: 'var(--text-secondary)' }}>Loading verified financial intelligence metrics...</div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="card" style={{ borderColor: 'var(--accent-rose)', margin: '2rem 0' }}>
        <div className="card-header">
          <div className="card-title" style={{ color: 'var(--accent-rose)' }}>
            <AlertTriangle size={18} /> Backend Telemetry Unavailable
          </div>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{error}</p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Ensure the FastAPI server is running with <code>uvicorn fkip.interfaces.api.main:app --port 8000</code>.
        </p>
      </div>
    );
  }

  const docCount = stats?.indexed_document_count ?? 0;
  const issuerCount = stats?.unique_issuers_count ?? 0;
  const sourceTypes = stats?.source_type_distribution ?? {};
  const years = stats?.publication_year_distribution ?? {};
  const topics = stats?.topic_distribution ?? {};
  const latestRun = stats?.latest_pipeline_metrics;
  const recentDocs = stats?.recent_documents ?? [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Welcome Banner */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.6) 100%)',
          border: '1px solid var(--border-medium)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-cyan)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
            <ShieldCheck size={14} /> Authoritative Financial Corpus
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff', marginBottom: '0.4rem' }}>
            Financial Knowledge & Intelligence Research Platform
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '680px', fontSize: '0.85rem' }}>
            Ingesting and indexing official regulatory publications, 10-K/10-Q corporate filings, and market commentary with traceable, chunk-level citations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-primary" onClick={() => onNavigate('research')}>
            <Sparkles size={15} /> Start AI Research
          </button>
          <button className="btn btn-secondary" onClick={() => onNavigate('explorer')}>
            <FileText size={15} /> Explore Documents
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">
            <FileText size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
            Indexed Documents
          </div>
          <div className="metric-value">{docCount}</div>
          <div className="metric-sub">
            {docCount > 0 ? 'Verified in metadata store' : 'Not available (run ingestion)'}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <Building2 size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
            Unique Issuers
          </div>
          <div className="metric-value">{issuerCount}</div>
          <div className="metric-sub">
            {issuerCount > 0 ? `${stats?.issuers.slice(0, 2).join(', ')}${issuerCount > 2 ? '...' : ''}` : 'No issuers indexed'}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <Layers size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
            Source Types
          </div>
          <div className="metric-value">{Object.keys(sourceTypes).length}</div>
          <div className="metric-sub">
            {Object.keys(sourceTypes).join(', ') || 'None recorded'}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <Calendar size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
            Publication Years
          </div>
          <div className="metric-value">{Object.keys(years).length}</div>
          <div className="metric-sub">
            {Object.keys(years).join(', ') || 'None recorded'}
          </div>
        </div>
      </div>

      {/* Two Column Section: Distributions + Latest Pipeline Ingestion */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Source & Year Breakdown */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Layers size={16} /> Source-Type Distribution
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verified Counts</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
            {Object.entries(sourceTypes).length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No source types indexed.</div>
            ) : (
              Object.entries(sourceTypes).map(([type, count]) => {
                const percent = Math.round((count / (docCount || 1)) * 100);
                return (
                  <div key={type}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {type.replace(/_/g, ' ')}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {count} ({percent}%)
                      </span>
                    </div>
                    <div style={{ height: '6px', background: 'var(--bg-muted)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${percent}%`,
                          background:
                            type === 'annual_report'
                              ? '#3b82f6'
                              : type === 'fca_regulatory'
                              ? '#8b5cf6'
                              : type === 'public_report'
                              ? '#10b981'
                              : '#f59e0b',
                        }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="card-header" style={{ marginTop: '1.5rem', marginBottom: '0.75rem' }}>
            <div className="card-title" style={{ fontSize: '0.9rem' }}>
              <Calendar size={15} /> Publication Year Coverage
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {Object.entries(years).length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Not available</div>
            ) : (
              Object.entries(years).map(([year, count]) => (
                <div
                  key={year}
                  style={{
                    padding: '0.35rem 0.75rem',
                    background: 'var(--bg-muted)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{year}</span>
                  <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>({count})</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Latest Pipeline Observability */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Clock size={16} /> Latest Ingestion Run
            </div>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
              onClick={() => onNavigate('operations')}
            >
              Operations Detail <ArrowRight size={13} />
            </button>
          </div>

          {latestRun ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 0.8rem', background: 'var(--bg-input)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
                  {latestRun.errors && latestRun.errors.length > 0 ? (
                    <AlertTriangle size={16} color="var(--accent-amber)" />
                  ) : (
                    <CheckCircle2 size={16} color="var(--accent-emerald)" />
                  )}
                  <span style={{ fontWeight: 600 }}>
                    {latestRun.errors && latestRun.errors.length > 0 ? 'Completed with errors' : 'Completed successfully'}
                  </span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Duration: {latestRun.duration_seconds}s
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
                <div style={{ padding: '0.6rem', background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SEEN</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{latestRun.sources_seen}</div>
                </div>
                <div style={{ padding: '0.6rem', background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>INGESTED</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)' }}>
                    {latestRun.documents_ingested}
                  </div>
                </div>
                <div style={{ padding: '0.6rem', background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ERRORS</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: (latestRun.errors?.length || 0) > 0 ? 'var(--accent-rose)' : 'inherit' }}>
                    {latestRun.errors?.length || 0}
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Run ID: <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{latestRun.run_id}</code>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No recent pipeline ingestion metrics file found. Run ingestion via CLI or verify <code>PIPELINE_METRICS_PATH</code>.
            </div>
          )}

          {/* Topics Preview */}
          <div className="card-header" style={{ marginTop: '1.25rem', marginBottom: '0.5rem' }}>
            <div className="card-title" style={{ fontSize: '0.9rem' }}>
              Financial Classification Topics
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
            {Object.entries(topics).map(([topic, count]) => (
              <span key={topic} className="badge badge-topic">
                {topic} <strong style={{ marginLeft: '4px', color: 'var(--accent-cyan)' }}>{count}</strong>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileText size={16} /> Indexed Financial Documents
          </div>
          <button className="btn btn-secondary" onClick={() => onNavigate('explorer')} style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}>
            View Full Catalogue <ArrowRight size={13} />
          </button>
        </div>

        {recentDocs.length === 0 ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No documents indexed yet. Run the batch ingestion command to populate the corpus.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Issuer</th>
                  <th>Source Type</th>
                  <th>Published</th>
                  <th>Topics</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentDocs.map((doc) => (
                  <tr key={doc.document_id}>
                    <td style={{ fontWeight: 600, maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.title}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{doc.issuer || 'Unknown'}</td>
                    <td>
                      <span
                        className={`badge ${
                          doc.source_type === 'annual_report'
                            ? 'badge-source-annual'
                            : doc.source_type === 'fca_regulatory'
                            ? 'badge-source-fca'
                            : doc.source_type === 'public_report'
                            ? 'badge-source-public'
                            : 'badge-source-news'
                        }`}
                      >
                        {doc.source_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {doc.published_at || '—'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                        {doc.topics.slice(0, 2).map((t) => (
                          <span key={t} className="badge badge-topic" style={{ fontSize: '0.65rem' }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '0.725rem', padding: '0.2rem 0.5rem' }}
                        onClick={() => onSelectDocument(doc.document_id)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
