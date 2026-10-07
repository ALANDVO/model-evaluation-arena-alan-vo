import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { ArenaEvaluationResponse, Dataset, ModelRun } from '../types/api';
import { BootstrapChart } from './BootstrapChart';
import { CalibrationCurve } from './CalibrationCurve';
import { MetricsTable } from './MetricsTable';

interface Props {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  onSelectDataset: (d: Dataset) => void;
  modelRuns: ModelRun[];
  evaluationResult: ArenaEvaluationResponse | null;
  onEvaluationComplete: (res: ArenaEvaluationResponse) => void;
}

export const ArenaBenchmarkView: React.FC<Props> = ({
  datasets, selectedDataset, onSelectDataset, modelRuns, evaluationResult, onEvaluationComplete,
}) => {
  const [selectedModelIds, setSelectedModelIds] = useState<number[]>([]);
  const [resamples, setResamples] = useState(500);
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (modelRuns.length > 0 && selectedModelIds.length === 0) {
      setSelectedModelIds(modelRuns.slice(0, 3).map((r) => r.id));
    }
  }, [modelRuns]);

  const toggleModel = (id: number) => {
    setSelectedModelIds((prev) => prev.includes(id) ? (prev.length > 1 ? prev.filter((m) => m !== id) : prev) : [...prev, id]);
  };

  const handleRunEvaluation = async () => {
    if (!selectedDataset || selectedModelIds.length === 0) return;
    try {
      setLoading(true); setErrorMsg(null);
      const res = await api.runEvaluation({ dataset_id: selectedDataset.id, model_run_ids: selectedModelIds, resamples, confidence_level: confidenceLevel });
      onEvaluationComplete(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Evaluation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="arena-view">
      <div className="card controls-card">
        <div className="arena-controls-header">
          <div className="control-group">
            <label className="control-label">Benchmark Dataset</label>
            <select className="input-select" value={selectedDataset?.id || ''} onChange={(e) => {
              const f = datasets.find((d) => d.id === Number(e.target.value)); if (f) onSelectDataset(f);
            }}>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.name} ({d.task_type.toUpperCase()}, N={d.item_count})</option>)}
            </select>
          </div>

          <div className="control-group">
            <label className="control-label">Bootstrap Resamples (B)</label>
            <input type="number" min="50" max="2000" step="50" value={resamples} onChange={(e) => setResamples(Number(e.target.value))} className="input-number" />
          </div>

          <div className="control-group">
            <label className="control-label">Confidence Level</label>
            <select className="input-select" value={confidenceLevel} onChange={(e) => setConfidenceLevel(Number(e.target.value))}>
              <option value="0.90">90% (α = 0.10)</option>
              <option value="0.95">95% (α = 0.05)</option>
              <option value="0.99">99% (α = 0.01)</option>
            </select>
          </div>

          <div className="control-action">
            <button className="run-arena-btn" disabled={loading || selectedModelIds.length === 0} onClick={handleRunEvaluation}>
              {loading ? 'Resampling...' : '⚔️ Run Arena Evaluation'}
            </button>
          </div>
        </div>

        <div className="model-selector-row">
          <span className="selector-title">Select Competing Models:</span>
          <div className="model-checkbox-list">
            {modelRuns.map((r) => (
              <label key={r.id} className="model-checkbox-label">
                <input type="checkbox" checked={selectedModelIds.includes(r.id)} onChange={() => toggleModel(r.id)} />
                <span className="checkbox-name">{r.name}</span>
                <span className="checkbox-arch">({r.architecture})</span>
              </label>
            ))}
          </div>
        </div>

        {errorMsg && <div className="alert-banner error-banner">{errorMsg}</div>}
      </div>

      {evaluationResult && (
        <div className="arena-results-container">
          <MetricsTable taskType={evaluationResult.task_type} models={evaluationResult.models} pairedTests={evaluationResult.paired_tests} />
          <div className="visuals-grid">
            <BootstrapChart models={evaluationResult.models} />
            {evaluationResult.calibration_diagrams && evaluationResult.calibration_diagrams.length > 0 && (
              <CalibrationCurve diagrams={evaluationResult.calibration_diagrams} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
