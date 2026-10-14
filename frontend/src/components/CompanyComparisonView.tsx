import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { CompanyComparisonResponse } from '../types/api';
import {
  GitCompare,
  Building2,
  AlertTriangle,
  ShieldAlert,
  Info,
} from 'lucide-react';

interface CompanyComparisonViewProps {
  availableIssuers?: string[];
}

export const CompanyComparisonView: React.FC<CompanyComparisonViewProps> = ({
  availableIssuers = [],
}) => {
  const [issuers, setIssuers] = useState<string[]>(availableIssuers);
  const [companyA, setCompanyA] = useState<string>('');
  const [companyB, setCompanyB] = useState<string>('');
  const [topic, setTopic] = useState<string>('Cybersecurity and technology risk');
  const [customTopic, setCustomTopic] = useState<string>('');
  const [isCustomTopic, setIsCustomTopic] = useState(false);
  const [limit, setLimit] = useState(3);

  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<CompanyComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const predefinedTopics = [
    'Cybersecurity and technology risk',
    'Operational resilience',
    'Regulatory compliance',
    'Business and financial risks',
    'Technology investment',
  ];

  // If issuers list isn't passed from props, fetch from overview
  useEffect(() => {
    if (availableIssuers.length > 0) {
      setIssuers(availableIssuers);
      if (!companyA && availableIssuers.length >= 2) {
        setCompanyA(availableIssuers[0]);
        setCompanyB(availableIssuers[1]);
      }
    } else {
      api.getOverview()
        .then((res) => {
          if (res.issuers && res.issuers.length > 0) {
            setIssuers(res.issuers);
            setCompanyA(res.issuers[0]);
            setCompanyB(res.issuers[1] || res.issuers[0]);
          }
        })
        .catch(() => {});
    }
  }, [availableIssuers]);

  const handleCompare = async () => {
    const selectedTopic = isCustomTopic ? customTopic.trim() : topic;
    if (!selectedTopic || !companyA || !companyB) {
      setError('Please select both companies and an analysis topic.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.compareCompanies(selectedTopic, companyA, companyB, limit);
      setComparison(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Company comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Configuration Header Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <GitCompare size={18} color="var(--accent-cyan)" /> Side-by-Side Financial Disclosure Comparison
            </div>
            <div className="card-subtitle">
              Bounded two-company comparison isolating actual retrieved filing passages per issuer.
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
            ISSUER-ISOLATED RETRIEVAL
          </div>
        </div>

        {/* Form Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          {/* Company A */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
              Company A (Primary Issuer)
            </label>
            <select
              className="select"
              value={companyA}
              onChange={(e) => setCompanyA(e.target.value)}
            >
              {issuers.map((iss) => (
                <option key={iss} value={iss} disabled={iss === companyB}>
                  {iss}
                </option>
              ))}
            </select>
          </div>

          {/* Company B */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
              Company B (Benchmark Issuer)
            </label>
            <select
              className="select"
              value={companyB}
              onChange={(e) => setCompanyB(e.target.value)}
            >
              {issuers.map((iss) => (
                <option key={iss} value={iss} disabled={iss === companyA}>
                  {iss}
                </option>
              ))}
            </select>
          </div>

          {/* Analysis Topic */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
              Analysis Disclosure Topic
            </label>
            <select
              className="select"
              value={isCustomTopic ? '__custom__' : topic}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setIsCustomTopic(true);
                } else {
                  setIsCustomTopic(false);
                  setTopic(e.target.value);
                }
              }}
            >
              {predefinedTopics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
              <option value="__custom__">Custom Analysis Topic...</option>
            </select>
          </div>
        </div>

        {isCustomTopic && (
          <div style={{ marginBottom: '1rem' }}>
            <input
              type="text"
              className="input"
              placeholder="Enter custom disclosure topic (e.g., Capital adequacy or Climate transition)..."
              value={customTopic}
              onChange={(e) => setCustomTopic(e.target.value)}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <span>Passages per company: <strong>{limit}</strong></span>
            <input
              type="range"
              min="1"
              max="6"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{ width: '80px', cursor: 'pointer' }}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={handleCompare}
            disabled={loading || !companyA || !companyB || companyA === companyB}
            style={{ padding: '0.6rem 1.4rem' }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: '15px', height: '15px' }} />
                Comparing Disclosures...
              </>
            ) : (
              <>
                <GitCompare size={15} /> Execute Comparison
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="card" style={{ borderColor: 'var(--accent-rose)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-rose)', fontWeight: 600 }}>
            <AlertTriangle size={16} /> Comparison Error
          </div>
          <p style={{ marginTop: '0.4rem', color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Comparison Synthesis / Notes Banner */}
          <div
            className="card"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
              borderLeft: '3px solid var(--accent-cyan)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
              <Info size={16} /> Objective Comparison Assessment
            </div>
            <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
              {comparison.comparison_notes}
            </p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Evaluation topic: <strong>{comparison.topic}</strong> • Grounded strictly in retrieved source filings
            </div>
          </div>

          {/* Side by Side Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
            {/* Company A Column */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Building2 size={18} color="var(--accent-blue)" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{comparison.company_a.issuer}</h3>
                </div>
                <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
                  {comparison.company_a.retrieval_count} passage{comparison.company_a.retrieval_count === 1 ? '' : 's'}
                </span>
              </div>

              {/* Evidence Gap Warning */}
              {comparison.company_a.evidence_gap ? (
                <div className="evidence-gap-box">
                  <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong>Evidence Gap Identified</strong>
                    <p style={{ marginTop: '0.25rem', fontSize: '0.8rem' }}>
                      {comparison.company_a.gap_reason || 'No disclosure passages directly addressing this topic were retrieved for this issuer in the current indexed corpus.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div style={{ background: 'var(--bg-input)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                    Extractive Synthesis
                  </div>
                  {comparison.company_a.summary}
                </div>
              )}

              {/* Source Documents */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Contributing Source Documents ({comparison.company_a.matching_documents.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {comparison.company_a.matching_documents.map((doc) => (
                    <div
                      key={doc.document_id}
                      style={{
                        padding: '0.4rem 0.6rem',
                        background: 'var(--bg-input)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.775rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '240px' }}>
                        {doc.title}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {doc.published_at || '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cited Excerpts */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Cited Excerpts
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {comparison.company_a.citations.map((c, i) => (
                    <div
                      key={c.chunk_id}
                      style={{
                        padding: '0.75rem',
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>Passage #{i + 1}</span>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>score: {c.score}</span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        "{c.excerpt}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Company B Column */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Building2 size={18} color="var(--accent-emerald)" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{comparison.company_b.issuer}</h3>
                </div>
                <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
                  {comparison.company_b.retrieval_count} passage{comparison.company_b.retrieval_count === 1 ? '' : 's'}
                </span>
              </div>

              {/* Evidence Gap Warning */}
              {comparison.company_b.evidence_gap ? (
                <div className="evidence-gap-box">
                  <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong>Evidence Gap Identified</strong>
                    <p style={{ marginTop: '0.25rem', fontSize: '0.8rem' }}>
                      {comparison.company_b.gap_reason || 'No disclosure passages directly addressing this topic were retrieved for this issuer in the current indexed corpus.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div style={{ background: 'var(--bg-input)', padding: '0.85rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                    Extractive Synthesis
                  </div>
                  {comparison.company_b.summary}
                </div>
              )}

              {/* Source Documents */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Contributing Source Documents ({comparison.company_b.matching_documents.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {comparison.company_b.matching_documents.map((doc) => (
                    <div
                      key={doc.document_id}
                      style={{
                        padding: '0.4rem 0.6rem',
                        background: 'var(--bg-input)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.775rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '240px' }}>
                        {doc.title}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {doc.published_at || '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cited Excerpts */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Cited Excerpts
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {comparison.company_b.citations.map((c, i) => (
                    <div
                      key={c.chunk_id}
                      style={{
                        padding: '0.75rem',
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                        <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>Passage #{i + 1}</span>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>score: {c.score}</span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        "{c.excerpt}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
