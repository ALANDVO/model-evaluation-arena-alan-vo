import { ArenaEvaluationResponse, Dataset, ModelRun, SessionInfo, AdvisoryAuditResponse, AuditLogEntry } from '../types/api';

class ApiClient {
  private csrfToken = '';
  private authToken = '';

  setCsrfToken(t: string) { this.csrfToken = t; }
  setAuthToken(t: string) { this.authToken = t; }

  private reqHeaders(contentType = 'application/json'): HeadersInit {
    const h: Record<string, string> = { Accept: 'application/json' };
    if (contentType) h['Content-Type'] = contentType;
    if (this.csrfToken) h['X-CSRF-Token'] = this.csrfToken;
    if (this.authToken) h['Authorization'] = `Bearer ${this.authToken}`;
    return h;
  }

  private async req<T>(url: string, opts: RequestInit = {}): Promise<T> {
    const res = await fetch(url, { credentials: 'include', headers: this.reqHeaders(), ...opts });
    if (!res.ok) {
      let msg = `Error ${res.status}: ${res.statusText}`;
      try { const b = await res.json(); if (b.detail) msg = b.detail; } catch {}
      throw new Error(msg);
    }
    return res.json() as Promise<T>;
  }

  async getSession(): Promise<SessionInfo> {
    const d = await this.req<SessionInfo>('/api/auth/session');
    if (d.csrf_token) this.setCsrfToken(d.csrf_token);
    return d;
  }

  async demoLogin(role: string): Promise<any> {
    const d = await this.req<any>('/api/auth/demo-login', { method: 'POST', body: JSON.stringify({ role }) });
    if (d.csrf_token) this.setCsrfToken(d.csrf_token);
    if (d.token) this.setAuthToken(d.token);
    return d;
  }

  async logout(): Promise<void> {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include', headers: this.reqHeaders() });
    this.authToken = '';
  }

  async listDatasets(taskType?: string): Promise<Dataset[]> {
    return this.req<Dataset[]>(taskType ? `/api/datasets?task_type=${taskType}` : '/api/datasets');
  }

  async getDataset(id: number): Promise<Dataset> {
    return this.req<Dataset>(`/api/datasets/${id}`);
  }

  async createDataset(payload: any): Promise<Dataset> {
    return this.req<Dataset>('/api/datasets', { method: 'POST', body: JSON.stringify(payload) });
  }

  async uploadDatasetItems(datasetId: number, items: any[]): Promise<any> {
    return this.req<any>(`/api/datasets/${datasetId}/items`, { method: 'POST', body: JSON.stringify(items) });
  }

  async listModelRuns(datasetId?: number): Promise<ModelRun[]> {
    return this.req<ModelRun[]>(datasetId ? `/api/models?dataset_id=${datasetId}` : '/api/models');
  }

  async createModelRun(payload: any): Promise<ModelRun> {
    return this.req<ModelRun>('/api/models', { method: 'POST', body: JSON.stringify(payload) });
  }

  async uploadPredictions(modelId: number, predictions: any[]): Promise<any> {
    return this.req<any>(`/api/models/${modelId}/predictions`, { method: 'POST', body: JSON.stringify({ predictions }) });
  }

  async runEvaluation(payload: any): Promise<ArenaEvaluationResponse> {
    return this.req<ArenaEvaluationResponse>('/api/evaluations/run', { method: 'POST', body: JSON.stringify(payload) });
  }

  async requestAdvisoryAudit(payload: any): Promise<AdvisoryAuditResponse> {
    return this.req<AdvisoryAuditResponse>('/api/llm/audit', { method: 'POST', body: JSON.stringify(payload) });
  }

  async listAuditLogs(): Promise<{ total: number; items: AuditLogEntry[] }> {
    return this.req<{ total: number; items: AuditLogEntry[] }>('/api/audit');
  }
}

export const api = new ApiClient();
