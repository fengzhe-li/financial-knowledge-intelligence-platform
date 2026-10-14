import type {
  CompanyComparisonResponse,
  DocumentCatalogResponse,
  DocumentChunk,
  DocumentDetail,
  FinancialAnalysisAnswer,
  OverviewStats,
  PipelineRun,
  PipelineStatsResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL ?? (window.location.port === '5173' ? '/api' : '');

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorMsg = `API request failed with status ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Fallback to text or generic message
        const text = await res.text().catch(() => '');
        if (text) errorMsg = text;
      }
      throw new ApiError(errorMsg, res.status);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError('Request timed out after 20 seconds', 408);
    }
    throw new ApiError(err instanceof Error ? err.message : 'Network error communicating with backend', 0);
  }
}

export const api = {
  async getHealth(): Promise<{ status: string; service: string }> {
    return request<{ status: string; service: string }>('/health');
  },

  async getOverview(): Promise<OverviewStats> {
    return request<OverviewStats>('/overview');
  },

  async getPipelineStats(): Promise<PipelineStatsResponse> {
    return request<PipelineStatsResponse>('/pipeline-stats');
  },

  async getPipelineRuns(limit = 10): Promise<PipelineRun[]> {
    return request<PipelineRun[]>(`/pipeline-runs?limit=${limit}`);
  },

  async listDocuments(params: {
    page?: number;
    pageSize?: number;
    q?: string;
    issuer?: string;
    sourceType?: string;
    year?: string;
  } = {}): Promise<DocumentCatalogResponse> {
    const query = new URLSearchParams();
    query.set('page', String(params.page || 1));
    query.set('page_size', String(params.pageSize || 10));
    if (params.q?.trim()) query.set('q', params.q.trim());
    if (params.issuer?.trim()) query.set('issuer', params.issuer.trim());
    if (params.sourceType?.trim()) query.set('source_type', params.sourceType.trim());
    if (params.year?.trim()) query.set('year', params.year.trim());

    return request<DocumentCatalogResponse>(`/documents?${query.toString()}`);
  },

  async getDocument(documentId: string): Promise<DocumentDetail> {
    return request<DocumentDetail>(`/documents/${encodeURIComponent(documentId)}`);
  },

  async getDocumentChunks(documentId: string): Promise<DocumentChunk[]> {
    return request<DocumentChunk[]>(`/documents/${encodeURIComponent(documentId)}/chunks`);
  },

  async searchDocuments(query: string, limit = 5): Promise<any[]> {
    return request<any[]>(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  },

  async answerQuestion(question: string, limit = 5): Promise<FinancialAnalysisAnswer> {
    return request<FinancialAnalysisAnswer>('/analysis/answer', {
      method: 'POST',
      body: JSON.stringify({ question, limit }),
    });
  },

  async compareCompanies(
    topic: string,
    issuerA: string,
    issuerB: string,
    limit = 4
  ): Promise<CompanyComparisonResponse> {
    return request<CompanyComparisonResponse>('/analysis/compare', {
      method: 'POST',
      body: JSON.stringify({
        topic,
        issuer_a: issuerA,
        issuer_b: issuerB,
        limit,
      }),
    });
  },
};
