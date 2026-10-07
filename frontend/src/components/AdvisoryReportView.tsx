import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AdvisoryAuditResponse, AuditLogEntry, Dataset, ModelRun } from '../types/api';

interface Props {
  selectedDataset: Dataset | null;
  modelRuns: ModelRun[];
  reportId?: number;
}

export const AdvisoryReportView: React.FC<Props> = ({ selectedDataset, modelRuns, reportId }) => {
  const [advisoryResult, setAdvisoryResult] = useState<AdvisoryAuditResponse | null>(null);
  const [loadingAdvisory, setLoadingAdvisory] = useState(false);
  const [advisoryError, setAdvisoryError] = useState<string | null>(null);
  const [userContext, setUserContext] = useState('');
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  const fetchAuditLogs = async () => {
    try {
      setLoadingAudit(true);
      const res = await api.listAuditLogs();
      setAuditLogs(res.items);
    } catch {} finally {
      setLoadingAudit(false);
    }
  };

  useEffect(() => { fetchAuditLogs(); }, []);

  const handleRequestAdvisory = async () => {
    if (!selectedDataset) return;
    try {
      setLoadingAdvisory(true);
      setAdvisoryError(null);
      const res = await api.requestAdvisoryAudit({
        dataset_id: selectedDataset.id,
        model_run_ids: modelRuns.map((r) => r.id),
        focus_metric: selectedDataset.task_type === 'classification' ? 'accuracy' : 'rmse',
        user_context: userContext.trim() || undefined,
      });
      setAdvisoryResult(res);
      fetchAuditLogs();
    } catch (err: any) {
      setAdvisoryError(err.message || 'Advisory request failed');
    } finally {
      setLoadingAdvisory(false);
    }
  };

  return (
    <div className="reports-view-grid">
      <div className="card">
        <div className="card-header flex-between">
          <div>
            <h2 className="card-title">Advisory LLM Diagnostic</h2>
            <p className="card-subtitle">Grounded in empirical bootstrap metrics and cohort slices</p>
          </div>
          {reportId && (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="secondary-btn" onClick={() => window.open(`/api/evaluations/export/${reportId}?format=json`, '_blank')}>JSON</button>
              <button className="secondary-btn" onClick={() => window.open(`/api/evaluations/export/${reportId}?format=csv`, '_blank')}>CSV</button>
            </div>
          )}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div className="form-group">
            <label>Auditor Focus Context (Optional)</label>
            <input type="text" value={userContext} onChange={(e) => setUserContext(e.target.value)} placeholder="e.g. Focus on senior demographic calibration" className="input-text" />
          </div>
          <button className="primary-btn" disabled={loadingAdvisory || !selectedDataset} onClick={handleRequestAdvisory}>
            {loadingAdvisory ? 'Generating...' : 'Generate Advisory Commentary'}
          </button>
        </div>

        {advisoryError && <div className="alert-banner error-banner">{advisoryError}</div>}

        {advisoryResult && (
          <div>
            <div className="advisory-disclaimer-box">
              <span className="disclaimer-title">Advisory Notice</span>
              <p>{advisoryResult.advisory_disclaimer}</p>
            </div>
            <div className="dataset-meta-row" style={{ margin: '0.5rem 0' }}>
              <span>Provider: <code>{advisoryResult.provider}</code></span>
              <span>Model: <code>{advisoryResult.model}</code></span>
              <span>Status: <span className="winner-tag">{advisoryResult.status}</span></span>
            </div>
            <div className="advisory-text-box"><pre>{advisoryResult.analysis}</pre></div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header flex-between">
          <div>
            <h2 className="card-title">System Audit Log</h2>
            <p className="card-subtitle">Immutable log of mutations and evaluations</p>
          </div>
          <button className="secondary-btn" onClick={fetchAuditLogs}>Refresh</button>
        </div>

        {loadingAudit ? (
          <div className="empty-notice">Loading audit entries...</div>
        ) : (
          <table className="mini-table">
            <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th></tr></thead>
            <tbody>
              {auditLogs.slice(0, 10).map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleTimeString()}</td>
                  <td><code>{log.user_id}</code></td>
                  <td><strong>{log.action}</strong></td>
                  <td>{log.resource_type} #{log.resource_id}</td>
                </tr>
              ))}
              {auditLogs.length === 0 && <tr><td colSpan={4} className="empty-notice">No audit records yet.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
