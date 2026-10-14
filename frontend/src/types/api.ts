export type SourceType =
  | 'annual_report'
  | 'financial_news'
  | 'fca_regulatory'
  | 'public_report'
  | 'research';

export interface DocumentSummary {
  document_id: string;
  title: string;
  source_type: SourceType;
  issuer: string | null;
  published_at: string | null;
  topics: string[];
}

export interface DocumentItem extends DocumentSummary {
  keywords?: string[];
  summary?: string;
  uri?: string;
}

export interface DocumentDetail {
  document_id: string;
  title: string;
  source_type: SourceType;
  issuer: string | null;
  published_at: string | null;
  summary: string;
  keywords: string[];
  topics: string[];
  uri: string;
  object_key: string;
  clean_text: string;
  created_at: string;
}

export interface DocumentChunk {
  chunk_id: string;
  chunk_index: number;
  start_char: number;
  end_char: number;
  text: string;
}

export interface DocumentCatalogResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  available_issuers: string[];
  available_source_types: string[];
  available_years: string[];
}

export interface Citation {
  document_id: string;
  title: string;
  issuer: string | null;
  published_at?: string | null;
  uri: string;
  chunk_id: string;
  chunk_index: number;
  score: number;
  excerpt: string;
}

export interface FinancialAnalysisAnswer {
  question: string;
  answer: string;
  retrieval_count: number;
  citations: Citation[];
}

export interface CompanyEvidence {
  issuer: string;
  topic: string;
  citations: Citation[];
  matching_documents: {
    document_id: string;
    title: string;
    published_at: string | null;
    source_type: string;
    uri: string;
  }[];
  retrieval_count: number;
  summary: string;
  evidence_gap: boolean;
  gap_reason: string | null;
}

export interface CompanyComparisonResponse {
  topic: string;
  issuer_a: string;
  issuer_b: string;
  company_a: CompanyEvidence;
  company_b: CompanyEvidence;
  comparison_notes: string;
}

export interface PipelineRun {
  run_id: string;
  status: string;
  manifest_path: string | null;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number;
  sources_seen: number;
  documents_ingested: number;
  documents_skipped: number;
  duplicate_sources: number;
  validation_failures: number;
  error_count: number;
  errors?: {
    source_uri: string;
    stage: string;
    message: string;
  }[];
  created_at: string;
}

export interface PipelineStatsResponse {
  available: boolean;
  metrics_path: string;
  message?: string;
  metrics?: {
    run_id: string;
    started_at: string;
    finished_at?: string;
    duration_seconds: number;
    sources_seen: number;
    documents_ingested: number;
    documents_skipped: number;
    duplicate_sources: number;
    validation_failures: number;
    errors: {
      source_uri: string;
      stage: string;
      message: string;
    }[];
    document_ids: string[];
  };
}

export interface OverviewStats {
  indexed_document_count: number;
  unique_issuers_count: number;
  issuers: string[];
  source_type_distribution: Record<string, number>;
  publication_year_distribution: Record<string, number>;
  topic_distribution: Record<string, number>;
  recent_documents: DocumentSummary[];
  recent_pipeline_runs: PipelineRun[];
  latest_pipeline_metrics: PipelineStatsResponse['metrics'] | null;
}
