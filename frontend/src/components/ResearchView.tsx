import React, { useState } from 'react';
import { api } from '../services/api';
import type { Citation, FinancialAnalysisAnswer } from '../types/api';
import {
  Search,
  Sparkles,
  AlertCircle,
  BookOpen,
  X,
  FileText,
  Info,
} from 'lucide-react';

export const ResearchView: React.FC = () => {
  const [question, setQuestion] = useState('What does the FCA mandate regarding operational resilience?');
  const [limit, setLimit] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FinancialAnalysisAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Selected citation for side drawer
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const sampleQuestions = [
    'What does the FCA mandate regarding operational resilience?',
    "What are Microsoft's primary cybersecurity and technology risk disclosures?",
    "What was Apple's iPhone and Services revenue performance?",
    'What did Barclays report regarding liquidity and capital discipline?',
  ];

  const handleSearch = async (queryText?: string) => {
    const q = (queryText || question).trim();
    if (!q) return;
    if (queryText) setQuestion(queryText);

    setLoading(true);
    setError(null);
    try {
      const res = await api.answerQuestion(q, limit);
      setResult(res);
      if (res.citations.length > 0) {
        setActiveCitation(res.citations[0]);
      } else {
        setActiveCitation(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis query failed');
    } finally {
      setLoading(false);
    }
  };

  // Render answer text with interactive clickable citation pills
  const renderInteractiveAnswer = (answerText: string, citations: Citation[]) => {
    // Regex matches [1], [2], etc.
    const parts = answerText.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationNumber = parseInt(match[1], 10);
        const citationObj = citations[citationNumber - 1];
        return (
          <button
            key={index}
            className="citation-marker"
            onClick={() => {
              if (citationObj) setActiveCitation(citationObj);
            }}
            title={citationObj ? `Click to inspect citation #${citationNumber}: ${citationObj.title}` : `Citation ${citationNumber}`}
          >
            [{citationNumber}]
          </button>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  const isInsufficientEvidence =
    result && (result.citations.length === 0 || result.answer.toLowerCase().includes('no relevant financial document evidence was found'));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Prompt Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Sparkles size={18} color="var(--accent-cyan)" /> Evidence-Based Financial AI Research
            </div>
            <div className="card-subtitle">
              Ask questions grounded directly in indexed financial filings, regulatory publications, and annual reports.
            </div>
          </div>
          <div
            style={{
              fontSize: '0.75rem',
              padding: '0.25rem 0.6rem',
              background: 'rgba(56, 189, 248, 0.1)',
              color: 'var(--accent-cyan)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              fontWeight: 600,
            }}
          >
            DETERMINISTIC EXTRACTIVE RAG
          </div>
        </div>

        {/* Suggested Queries */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Verified Research Queries
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {sampleQuestions.map((q) => (
              <button
                key={q}
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                onClick={() => handleSearch(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Question Input Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              className="input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter your financial document research question..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch();
              }}
              style={{ fontSize: '0.95rem', padding: '0.75rem 1rem' }}
            />
            <button
              className="btn btn-primary"
              disabled={loading || !question.trim()}
              onClick={() => handleSearch()}
              style={{ padding: '0.75rem 1.5rem', whiteSpace: 'nowrap' }}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: '16px', height: '16px' }} />
                  Retrieving...
                </>
              ) : (
                <>
                  <Search size={16} /> Run Analysis
                </>
              )}
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span>Max evidence chunks: <strong>{limit}</strong></span>
              <input
                type="range"
                min="1"
                max="8"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                style={{ width: '100px', cursor: 'pointer' }}
              />
            </div>
            <span>Grounding: 100% extractive from verified source text</span>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-rose)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-rose)', fontWeight: 600 }}>
            <AlertCircle size={18} /> Analysis Error
          </div>
          <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: activeCitation ? '1fr 380px' : '1fr', gap: '1.5rem' }}>
          {/* Main Answer Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Answer Box */}
            <div className="card" style={{ borderLeft: '3px solid var(--accent-cyan)' }}>
              <div className="card-header">
                <div className="card-title">
                  <BookOpen size={17} /> Extractive Financial Synthesis
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="badge" style={{ background: 'var(--bg-muted)', color: 'var(--text-highlight)' }}>
                    {result.retrieval_count} passage{result.retrieval_count === 1 ? '' : 's'} retrieved
                  </span>
                </div>
              </div>

              {isInsufficientEvidence ? (
                <div className="evidence-gap-box">
                  <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong style={{ display: 'block', marginBottom: '0.25rem' }}>Insufficient Direct Evidence</strong>
                    The indexed financial corpus does not contain sufficiently relevant passages to verify an answer for this query. The platform refrains from fabricating conclusions when source documents lack matching disclosures.
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '0.95rem', lineHeight: 1.7, color: 'var(--text-primary)' }}>
                  {renderInteractiveAnswer(result.answer, result.citations)}
                </div>
              )}

              <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <Info size={13} />
                <span>
                  Click any numbered bracket <span className="citation-marker" style={{ pointerEvents: 'none' }}>[#]</span> or citation card to inspect the exact underlying passage.
                </span>
              </div>
            </div>

            {/* Citations List */}
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Cited Source Evidence Passages ({result.citations.length})
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {result.citations.map((citation, index) => {
                  const citationIndex = index + 1;
                  const isSelected = activeCitation?.chunk_id === citation.chunk_id;
                  return (
                    <div
                      key={citation.chunk_id}
                      className="card"
                      onClick={() => setActiveCitation(citation)}
                      style={{
                        cursor: 'pointer',
                        borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                        background: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                        boxShadow: isSelected ? 'var(--shadow-glow)' : 'var(--shadow-sm)',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span
                            className="citation-marker"
                            style={{
                              background: isSelected ? 'var(--accent-cyan)' : undefined,
                              color: isSelected ? '#0b1120' : undefined,
                            }}
                          >
                            [{citationIndex}]
                          </span>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{citation.title}</span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span
                            style={{
                              fontSize: '0.725rem',
                              fontFamily: 'var(--font-mono)',
                              padding: '0.15rem 0.4rem',
                              borderRadius: '4px',
                              background: 'var(--bg-muted)',
                              color: 'var(--accent-cyan)',
                            }}
                          >
                            score: {citation.score}
                          </span>
                        </div>
                      </div>

                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.5rem' }}>
                        "{citation.excerpt}"
                      </p>

                      <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                        <span>
                          <strong>Issuer:</strong> {citation.issuer || 'Unknown'}
                        </span>
                        {citation.published_at && (
                          <>
                            <span>•</span>
                            <span>
                              <strong>Date:</strong> {citation.published_at}
                            </span>
                          </>
                        )}
                        <span>•</span>
                        <span>
                          <strong>Chunk:</strong> #{citation.chunk_index}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Citation Detail Panel */}
          {activeCitation && (
            <div className="card" style={{ position: 'sticky', top: '5rem', height: 'fit-content', border: '1px solid var(--border-medium)' }}>
              <div className="card-header" style={{ marginBottom: '0.75rem' }}>
                <div className="card-title" style={{ fontSize: '0.9rem' }}>
                  <FileText size={15} color="var(--accent-cyan)" /> Selected Passage Inspector
                </div>
                <button
                  onClick={() => setActiveCitation(null)}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                >
                  <X size={15} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ background: 'var(--bg-input)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    Exact Indexed Excerpt
                  </div>
                  <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', lineHeight: 1.6, fontStyle: 'italic' }}>
                    "{activeCitation.excerpt}"
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
                  <div>
                    <strong>Document:</strong> {activeCitation.title}
                  </div>
                  <div>
                    <strong>Issuer:</strong> {activeCitation.issuer || 'Unknown'}
                  </div>
                  {activeCitation.published_at && (
                    <div>
                      <strong>Published:</strong> {activeCitation.published_at}
                    </div>
                  )}
                  <div>
                    <strong>Relevance Score:</strong>{' '}
                    <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{activeCitation.score}</code>{' '}
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>(Cosine similarity)</span>
                  </div>
                  <div>
                    <strong>Chunk Identity:</strong>{' '}
                    <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.725rem' }}>
                      {activeCitation.chunk_id}
                    </code>
                  </div>
                  <div>
                    <strong>Source URI:</strong>{' '}
                    <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.725rem', wordBreak: 'break-all' }}>
                      {activeCitation.uri}
                    </code>
                  </div>
                </div>

                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--bg-muted)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', marginTop: '0.5rem' }}>
                  Similarity scores quantify Blake2b word-hash feature alignment and do not represent calibrated statistical probabilities of correctness.
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
