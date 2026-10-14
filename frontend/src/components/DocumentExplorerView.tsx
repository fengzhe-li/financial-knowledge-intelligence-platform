import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { DocumentCatalogResponse, DocumentChunk, DocumentDetail, DocumentItem } from '../types/api';
import {
  Search,
  Filter,
  X,
  FileText,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
} from 'lucide-react';

interface DocumentExplorerViewProps {
  initialDocumentId?: string | null;
  onClearInitialDocument?: () => void;
}

export const DocumentExplorerView: React.FC<DocumentExplorerViewProps> = ({
  initialDocumentId,
  onClearInitialDocument,
}) => {
  const [catalog, setCatalog] = useState<DocumentCatalogResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [query, setQuery] = useState('');
  const [selectedIssuer, setSelectedIssuer] = useState('');
  const [selectedSourceType, setSelectedSourceType] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 8;

  // Selected document modal state
  const [selectedDocId, setSelectedDocId] = useState<string | null>(initialDocumentId || null);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailTab, setDetailTab] = useState<'metadata' | 'text' | 'chunks'>('metadata');
  const [copied, setCopied] = useState(false);

  // Fetch catalog function
  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listDocuments({
        page,
        pageSize,
        q: query,
        issuer: selectedIssuer,
        sourceType: selectedSourceType,
        year: selectedYear,
      });
      setCatalog(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load document catalog');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, query, selectedIssuer, selectedSourceType, selectedYear]);

  useEffect(() => {
    fetchCatalog();
  }, [fetchCatalog]);

  // Handle initial document ID from overview
  useEffect(() => {
    if (initialDocumentId) {
      setSelectedDocId(initialDocumentId);
      if (onClearInitialDocument) onClearInitialDocument();
    }
  }, [initialDocumentId, onClearInitialDocument]);

  // Fetch document detail
  useEffect(() => {
    if (!selectedDocId) {
      setDocDetail(null);
      setDocChunks([]);
      return;
    }

    let isMounted = true;
    setDetailLoading(true);

    Promise.all([
      api.getDocument(selectedDocId),
      api.getDocumentChunks(selectedDocId),
    ])
      .then(([detail, chunks]) => {
        if (isMounted) {
          setDocDetail(detail);
          setDocChunks(chunks);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('Failed to load document detail:', err);
        }
      })
      .finally(() => {
        if (isMounted) setDetailLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedDocId]);

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleResetFilters = () => {
    setQuery('');
    setSelectedIssuer('');
    setSelectedSourceType('');
    setSelectedYear('');
    setPage(1);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Title & Filter Bar */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <FileText size={18} /> Financial Document Explorer
            </div>
            <div className="card-subtitle">
              Browse, search and inspect indexed financial disclosures and regulatory publications
            </div>
          </div>
          {catalog && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              Showing {catalog.items.length} of <strong>{catalog.total}</strong> documents
            </div>
          )}
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
          {/* Search Input */}
          <div style={{ position: 'relative', flex: '1 1 240px' }}>
            <Search
              size={15}
              style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
            />
            <input
              type="text"
              className="input"
              placeholder="Search by title, issuer, keyword..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              style={{ paddingLeft: '32px' }}
            />
            {query && (
              <button
                onClick={() => {
                  setQuery('');
                  setPage(1);
                }}
                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Issuer Select */}
          <div style={{ minWidth: '160px', flex: '1 1 160px' }}>
            <select
              className="select"
              value={selectedIssuer}
              onChange={(e) => {
                setSelectedIssuer(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Issuers</option>
              {catalog?.available_issuers.map((iss) => (
                <option key={iss} value={iss}>
                  {iss}
                </option>
              ))}
            </select>
          </div>

          {/* Source Type Select */}
          <div style={{ minWidth: '150px', flex: '1 1 150px' }}>
            <select
              className="select"
              value={selectedSourceType}
              onChange={(e) => {
                setSelectedSourceType(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Source Types</option>
              {catalog?.available_source_types.map((st) => (
                <option key={st} value={st}>
                  {st.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Year Select */}
          <div style={{ minWidth: '110px', flex: '1 1 110px' }}>
            <select
              className="select"
              value={selectedYear}
              onChange={(e) => {
                setSelectedYear(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Years</option>
              {catalog?.available_years.map((yr) => (
                <option key={yr} value={yr}>
                  {yr}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          {(query || selectedIssuer || selectedSourceType || selectedYear) && (
            <button className="btn btn-secondary" onClick={handleResetFilters} style={{ fontSize: '0.8rem', padding: '0.5rem 0.75rem' }}>
              <Filter size={13} /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Catalog Table */}
      <div className="card">
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 0', gap: '0.75rem' }}>
            <div className="spinner" />
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Querying document metadata...</div>
          </div>
        ) : error ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--accent-rose)' }}>
            <p>{error}</p>
            <button className="btn btn-secondary" onClick={fetchCatalog} style={{ marginTop: '0.75rem' }}>
              Retry
            </button>
          </div>
        ) : !catalog || catalog.items.length === 0 ? (
          <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <FileText size={32} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
            <p style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>No matching documents found</p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
              Try adjusting your search criteria or resetting filters.
            </p>
          </div>
        ) : (
          <>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title & Provenance</th>
                    <th>Issuer</th>
                    <th>Source Type</th>
                    <th>Publication Date</th>
                    <th>Classified Topics</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {catalog.items.map((doc: DocumentItem) => (
                    <tr key={doc.document_id}>
                      <td style={{ maxWidth: '300px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {doc.title}
                        </div>
                        <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                          ID: {doc.document_id.slice(0, 18)}...
                        </div>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{doc.issuer || 'Unknown'}</td>
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
                          {doc.topics && doc.topics.length > 0 ? (
                            doc.topics.map((t) => (
                              <span key={t} className="badge badge-topic">
                                {t}
                              </span>
                            ))
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>General</span>
                          )}
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                          onClick={() => setSelectedDocId(doc.document_id)}
                        >
                          Inspect Detail
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {catalog.total_pages > 1 && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '0.5rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Page {catalog.page} of {catalog.total_pages}
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.35rem 0.7rem', fontSize: '0.8rem' }}
                    disabled={catalog.page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft size={14} /> Previous
                  </button>

                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.35rem 0.7rem', fontSize: '0.8rem' }}
                    disabled={catalog.page >= catalog.total_pages}
                    onClick={() => setPage((p) => Math.min(catalog.total_pages, p + 1))}
                  >
                    Next <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Document Detail Modal */}
      {selectedDocId && (
        <div className="modal-overlay" onClick={() => setSelectedDocId(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <FileText size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Document Provenance & Extraction Detail</h3>
              </div>
              <button
                onClick={() => setSelectedDocId(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            {detailLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem', gap: '0.75rem' }}>
                <div className="spinner" />
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Retrieving full document text and chunks...</div>
              </div>
            ) : docDetail ? (
              <>
                <div style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-input)', padding: '0.75rem 1.25rem', display: 'flex', gap: '1rem' }}>
                  <button
                    className={`btn ${detailTab === 'metadata' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.775rem', padding: '0.3rem 0.7rem' }}
                    onClick={() => setDetailTab('metadata')}
                  >
                    Metadata & Summary
                  </button>
                  <button
                    className={`btn ${detailTab === 'text' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.775rem', padding: '0.3rem 0.7rem' }}
                    onClick={() => setDetailTab('text')}
                  >
                    Extracted Clean Text ({docDetail.clean_text ? `${Math.round(docDetail.clean_text.length / 1024)} KB` : '0 KB'})
                  </button>
                  <button
                    className={`btn ${detailTab === 'chunks' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.775rem', padding: '0.3rem 0.7rem' }}
                    onClick={() => setDetailTab('chunks')}
                  >
                    Indexed Chunks ({docChunks.length})
                  </button>
                </div>

                <div className="modal-body">
                  {detailTab === 'metadata' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                          {docDetail.title}
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          <span>
                            <strong>Issuer:</strong> {docDetail.issuer || 'Unknown'}
                          </span>
                          <span>•</span>
                          <span>
                            <strong>Published:</strong> {docDetail.published_at || 'Not recorded'}
                          </span>
                          <span>•</span>
                          <span>
                            <strong>Type:</strong> {docDetail.source_type}
                          </span>
                        </div>
                      </div>

                      <div style={{ background: 'var(--bg-input)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                          Deterministic 3-Sentence Extractive Summary
                        </div>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                          {docDetail.summary || 'No summary available.'}
                        </p>
                      </div>

                      {docDetail.keywords && docDetail.keywords.length > 0 && (
                        <div>
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                            Extracted Keywords
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                            {docDetail.keywords.map((kw) => (
                              <span key={kw} className="badge" style={{ background: 'var(--bg-muted)', color: 'var(--text-secondary)' }}>
                                {kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.775rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
                        <div><strong>Document ID (UUIDv5):</strong> <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{docDetail.document_id}</code></div>
                        <div><strong>Object Key:</strong> <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{docDetail.object_key}</code></div>
                        <div><strong>Source URI:</strong> <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{docDetail.uri}</code></div>
                        <div><strong>Ingested At:</strong> {new Date(docDetail.created_at).toLocaleString()}</div>
                      </div>
                    </div>
                  )}

                  {detailTab === 'text' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                          Showing extracted and normalized plain text stored in object storage.
                        </span>
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: '0.725rem', padding: '0.2rem 0.5rem' }}
                          onClick={() => handleCopyText(docDetail.clean_text)}
                        >
                          {copied ? <Check size={12} color="var(--accent-emerald)" /> : <Copy size={12} />}
                          {copied ? 'Copied' : 'Copy Text'}
                        </button>
                      </div>
                      <pre
                        style={{
                          background: 'var(--bg-input)',
                          padding: '1rem',
                          borderRadius: 'var(--radius-md)',
                          fontSize: '0.775rem',
                          fontFamily: 'var(--font-mono)',
                          whiteSpace: 'pre-wrap',
                          maxHeight: '450px',
                          overflowY: 'auto',
                          lineHeight: 1.6,
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        {docDetail.clean_text || 'No clean text stored.'}
                      </pre>
                    </div>
                  )}

                  {detailTab === 'chunks' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                        {docChunks.length} passages indexed with 120-word windows and 20-word overlap.
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '450px', overflowY: 'auto' }}>
                        {docChunks.map((chunk) => (
                          <div
                            key={chunk.chunk_id}
                            style={{
                              background: 'var(--bg-input)',
                              border: '1px solid var(--border-subtle)',
                              borderRadius: 'var(--radius-md)',
                              padding: '0.75rem',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontFamily: 'var(--font-mono)' }}>
                              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Chunk #{chunk.chunk_index}</span>
                              <span>Offsets: [{chunk.start_char}..{chunk.end_char}]</span>
                            </div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                              {chunk.text}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="modal-footer">
                  <button className="btn btn-secondary" onClick={() => setSelectedDocId(null)}>
                    Close
                  </button>
                </div>
              </>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                Document details could not be loaded.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
