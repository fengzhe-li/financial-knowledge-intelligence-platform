import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import type { NavTab } from './components/Header';
import { OverviewView } from './components/OverviewView';
import { DocumentExplorerView } from './components/DocumentExplorerView';
import { ResearchView } from './components/ResearchView';
import { CompanyComparisonView } from './components/CompanyComparisonView';
import { PipelineOperationsView } from './components/PipelineOperationsView';
import { api } from './services/api';
import type { OverviewStats } from './types/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'online' | 'connecting' | 'offline'>('connecting');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    try {
      const health = await api.getHealth();
      if (health.status === 'ok') {
        setBackendStatus('online');
      }
      const data = await api.getOverview();
      setStats(data);
      setStatsError(null);
    } catch (err: unknown) {
      setBackendStatus('offline');
      setStatsError(err instanceof Error ? err.message : 'Unable to connect to FastAPI backend');
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    loadOverview();
    const interval = setInterval(loadOverview, 30000);
    return () => clearInterval(interval);
  }, [loadOverview]);

  const handleSelectDocumentFromOverview = (docId: string) => {
    setSelectedDocId(docId);
    setActiveTab('explorer');
  };

  return (
    <div className="app-container">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        backendStatus={backendStatus}
        documentCount={stats?.indexed_document_count}
      />

      <main className="main-content">
        {activeTab === 'overview' && (
          <OverviewView
            stats={stats}
            loading={loadingStats}
            error={statsError}
            onNavigate={setActiveTab}
            onSelectDocument={handleSelectDocumentFromOverview}
          />
        )}

        {activeTab === 'explorer' && (
          <DocumentExplorerView
            initialDocumentId={selectedDocId}
            onClearInitialDocument={() => setSelectedDocId(null)}
          />
        )}

        {activeTab === 'research' && <ResearchView />}

        {activeTab === 'comparison' && (
          <CompanyComparisonView availableIssuers={stats?.issuers || []} />
        )}

        {activeTab === 'operations' && <PipelineOperationsView />}
      </main>

      <footer className="app-footer">
        <div>
          Financial Knowledge Intelligence Platform • Grounded Regulatory & Disclosure Research
        </div>
        <div>
          Portfolio Project by <strong>Fengzhe Li</strong> (<code>fengzheli048@gmail.com</code> / GitHub: <code>fengzhe-li</code>)
        </div>
      </footer>
    </div>
  );
};

export default App;
