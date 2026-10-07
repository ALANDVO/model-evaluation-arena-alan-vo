import React, { useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Dataset } from '../types/api';

interface Props {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  onSelectDataset: (d: Dataset) => void;
  onRefresh: () => void;
}

export const DatasetManager: React.FC<Props> = ({ datasets, selectedDataset, onSelectDataset, onRefresh }) => {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [taskType, setTaskType] = useState('classification');
  const [targetColumn, setTargetColumn] = useState('label');
  const [cohortInput, setCohortInput] = useState('cohort_a, cohort_b');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const canCreate = user?.roles?.some((r) => ['analyst', 'admin'].includes(r));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setFormError(null);
      const cohorts = cohortInput.split(',').map((s) => s.trim()).filter(Boolean);
      const created = await api.createDataset({ name, description, task_type: taskType, target_column: targetColumn, cohort_columns: cohorts });
      setShowModal(false);
      setName(''); setDescription('');
      onRefresh();
      onSelectDataset(created);
    } catch (err: any) {
      setFormError(err.message || 'Creation failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="dataset-manager-grid">
      <div className="card">
        <div className="card-header flex-between">
          <div>
            <h2 className="card-title">Benchmark Datasets</h2>
            <p className="card-subtitle">Ground-truth test datasets with cohort metadata</p>
          </div>
          {canCreate && <button className="primary-btn" onClick={() => setShowModal(true)}>+ New Dataset</button>}
        </div>

        <div className="dataset-list">
          {datasets.map((d) => (
            <div key={d.id} className={`dataset-card-item ${selectedDataset?.id === d.id ? 'active' : ''}`} onClick={() => onSelectDataset(d)}>
              <div className="dataset-item-header">
                <span className="dataset-name">{d.name}</span>
                <span className={`task-badge ${d.task_type}`}>{d.task_type}</span>
              </div>
              <p className="dataset-desc">{d.description || 'No description provided.'}</p>
              <div className="dataset-meta-row">
                <span>Items: <strong>{d.item_count}</strong></span>
                <span>Cohorts: <strong>{d.cohort_columns.join(', ') || 'None'}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        {selectedDataset ? (
          <div>
            <div className="card-header">
              <h2 className="card-title">{selectedDataset.name} (Inspection)</h2>
              <p className="card-subtitle">Task: {selectedDataset.task_type} &bull; Target: <code>{selectedDataset.target_column}</code></p>
            </div>
            <div className="dataset-detail-body">
              <p>{selectedDataset.description}</p>
              <div className="dataset-meta-row" style={{ marginTop: '0.75rem' }}>
                <span>Registered Cohorts: <strong>{selectedDataset.cohort_columns.join(', ') || 'None'}</strong></span>
                <span>Records: <strong>{selectedDataset.item_count}</strong></span>
              </div>
              {selectedDataset.sample_items && selectedDataset.sample_items.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <h3 className="section-title">Sample Test Items</h3>
                  <table className="mini-table">
                    <thead><tr><th>Key</th><th>Ground Truth</th><th>Cohorts</th></tr></thead>
                    <tbody>
                      {selectedDataset.sample_items.slice(0, 6).map((it) => (
                        <tr key={it.id}><td><code>{it.item_key}</code></td><td><strong>{it.ground_truth}</strong></td><td>{JSON.stringify(it.cohorts)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="empty-notice">Select a dataset to view specifications.</div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-dialog">
            <h3 className="modal-title">Create Benchmark Dataset</h3>
            {formError && <div className="alert-banner error-banner">{formError}</div>}
            <form onSubmit={handleCreate}>
              <div className="form-group"><label>Dataset Name</label><input type="text" required value={name} onChange={(e) => setName(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Task Type</label>
                <select value={taskType} onChange={(e) => setTaskType(e.target.value)} className="input-select">
                  <option value="classification">Classification</option>
                  <option value="regression">Regression</option>
                </select>
              </div>
              <div className="form-group"><label>Target Column</label><input type="text" value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Cohort Columns (comma-separated)</label><input type="text" value={cohortInput} onChange={(e) => setCohortInput(e.target.value)} className="input-text" /></div>
              <div className="form-group"><label>Description</label><textarea value={description} onChange={(e) => setDescription(e.target.value)} className="input-textarea" rows={2} /></div>
              <div className="modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" disabled={submitting} className="primary-btn">{submitting ? 'Creating...' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
