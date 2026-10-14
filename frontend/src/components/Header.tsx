import React from 'react';
import {
  BarChart3,
  FileText,
  Search,
  GitCompare,
  Activity,
  Layers,
} from 'lucide-react';

export type NavTab = 'overview' | 'explorer' | 'research' | 'comparison' | 'operations';

interface HeaderProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  backendStatus: 'online' | 'connecting' | 'offline';
  documentCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  backendStatus,
  documentCount,
}) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <Layers size={20} />
        </div>
        <div className="brand-text">
          <h1>
            FKIP Research Workspace
            <span
              style={{
                fontSize: '0.65rem',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                fontWeight: 600,
                textTransform: 'uppercase',
              }}
            >
              v1.0
            </span>
          </h1>
          <p>Evidence-First Financial Intelligence & Regulatory Analytics</p>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => onTabChange('overview')}
        >
          <BarChart3 size={15} />
          Overview
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'explorer' ? 'active' : ''}`}
          onClick={() => onTabChange('explorer')}
        >
          <FileText size={15} />
          Document Explorer
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'research' ? 'active' : ''}`}
          onClick={() => onTabChange('research')}
        >
          <Search size={15} />
          AI Research
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
          onClick={() => onTabChange('comparison')}
        >
          <GitCompare size={15} />
          Company Comparison
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'operations' ? 'active' : ''}`}
          onClick={() => onTabChange('operations')}
        >
          <Activity size={15} />
          Pipeline Ops
        </button>
      </nav>

      <div className="header-status">
        {typeof documentCount === 'number' && (
          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <span style={{ color: 'var(--text-highlight)', fontWeight: 600 }}>{documentCount}</span> docs indexed
          </div>
        )}

        <div className={`status-badge ${backendStatus}`}>
          <span className="pulse-dot" />
          {backendStatus === 'online' ? 'FASTAPI CONNECTED' : backendStatus === 'connecting' ? 'CONNECTING...' : 'BACKEND OFFLINE'}
        </div>
      </div>
    </header>
  );
};
