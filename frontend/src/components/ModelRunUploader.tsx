import React, { useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Dataset, ModelRun } from '../types/api';

interface Props {
  dataset: Dataset;
  runs: ModelRun[];
  onRefreshRuns: () => void;
}

export const ModelRunUploader: React.FC<Props> = ({ dataset, runs, onRefreshRuns }) => {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [architecture, setArchitecture] = useState('LLM-ZeroShot');
  const [version, setVersion] = useState('1.0.0');
  const [predictionsInput, setPredictionsInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const canEdit = user?.roles?.some((r) => ['analyst', 'admin'].includes(r));

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setErrorMsg(null);
      const run = await api.createModelRun({ dataset_id: dataset.id, name, architecture, version });
      if (predictionsInput.trim()) {
        const parsed = JSON.parse(predictionsInput);
        if (Array.isArray(parsed) && parsed.length > 0) {
          await api.uploadPredictions(run.id, parsed);
        }
      }
      setShowModal(false);
      setName(''); setPredictionsInput('');
      onRefreshRuns();
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card model-runs-card">
      <div className="card-header flex-between">
        <div>
          <h2 className="card-title">Model Runs for {dataset.name}</h2>
          <p className="card-subtitle">Competing model checkpoints with uploaded predictions</p>
        </div>
        {canEdit && <button className="secondary-btn" onClick={() => setShowModal(true)}>+ Register Model</button>}
      </div>

      <div className="runs-grid">
        {runs.map((r) => (
          <div key={r.id} className="run-card">
            <div className="run-card-header"><span className="run-name">{r.name}</span><span className="run-version">v{r.version}</span></div>
            <div className="run-arch">Arch: {r.architecture}</div>
            <div className="run-stats"><span>Predictions: <strong>{r.prediction_count}</strong></span><span>By: {r.created_by}</span></div>
          </div>
        ))}
        {runs.length === 0 && <div className="empty-notice">No model runs registered for this dataset yet.</div>}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-dialog">
            <h3 className="modal-title">Register Model Run</h3>
            {errorMsg && <div className="alert-banner error-banner">{errorMsg}</div>}
            <form onSubmit={handleRegister}>
              <div className="form-group"><label>Model Name</label><input type="text" required value={name} onChange={(e) => setName(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Architecture</label><input type="text" value={architecture} onChange={(e) => setArchitecture(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Version</label><input type="text" value={version} onChange={(e) => setVersion(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Predictions JSON (Optional)</label><textarea value={predictionsInput} onChange={(e) => setPredictionsInput(e.target.value)} className="input-textarea" rows={3} placeholder='[{"item_key":"cust_0001","predicted_label":"1","probability":0.88}]' /></div>
              <div className="modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" disabled={submitting} className="primary-btn">{submitting ? 'Registering...' : 'Register'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
