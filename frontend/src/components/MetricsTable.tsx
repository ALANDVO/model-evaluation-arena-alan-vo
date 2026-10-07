import React from 'react';
import { ModelMetrics, PairedHypothesisResult, TaskType } from '../types/api';

interface MetricsTableProps {
  taskType: TaskType;
  models: ModelMetrics[];
  pairedTests: PairedHypothesisResult[];
}

export const MetricsTable: React.FC<MetricsTableProps> = ({ taskType, models, pairedTests }) => {
  if (models.length === 0) {
    return <div className="empty-notice">No models selected for evaluation.</div>;
  }

  const metricKeys = Object.keys(models[0].metrics);

  // Determine top model per metric
  const bestModelPerMetric: Record<string, number> = {};
  metricKeys.forEach((key) => {
    let bestVal = models[0].metrics[key] ?? 0;
    let bestId = models[0].model_run_id;
    const lowerIsBetter = ['mse', 'rmse', 'mae', 'brier_score', 'log_loss', 'expected_calibration_error'].includes(key);

    models.forEach((m) => {
      const v = m.metrics[key] ?? 0;
      if (lowerIsBetter ? v < bestVal : v > bestVal) {
        bestVal = v;
        bestId = m.model_run_id;
      }
    });
    bestModelPerMetric[key] = bestId;
  });

  return (
    <div className="card metrics-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Comparative Metrics & 95% Bootstrap Confidence Intervals</h2>
          <p className="card-subtitle">Task: {taskType.toUpperCase()} &bull; Non-parametric percentile bootstrap resampling (α = 0.05)</p>
        </div>
      </div>

      <div className="table-responsive">
        <table className="arena-table">
          <thead>
            <tr>
              <th>Evaluation Metric</th>
              {models.map((m) => (
                <th key={m.model_run_id}>
                  <div className="model-col-header">
                    <span className="model-name">{m.model_name}</span>
                    <span className="model-sample-size">N={m.sample_size}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metricKeys.map((key) => (
              <tr key={key}>
                <td className="metric-name-cell">
                  <code>{key}</code>
                </td>
                {models.map((m) => {
                  const ci = m.bootstrap_cis[key];
                  const isBest = bestModelPerMetric[key] === m.model_run_id;
                  const point = m.metrics[key];

                  return (
                    <td key={m.model_run_id} className={`metric-val-cell ${isBest ? 'winner-cell' : ''}`}>
                      <div className="metric-score">
                        <span className="score-val">{point !== undefined ? point.toFixed(4) : '-'}</span>
                        {isBest && <span className="winner-tag">Leader</span>}
                      </div>
                      {ci && (
                        <div className="ci-badge">
                          95% CI: [{ci.ci_lower.toFixed(4)}, {ci.ci_upper.toFixed(4)}]
                          <span className="se-val"> (SE: {ci.standard_error.toFixed(4)})</span>
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pairedTests.length > 0 && (
        <div className="paired-tests-section">
          <h3 className="section-title">Paired Statistical Hypothesis Testing</h3>
          <div className="paired-grid">
            {pairedTests.map((pt, idx) => (
              <div key={idx} className={`paired-card ${pt.statistically_significant ? 'sig-card' : ''}`}>
                <div className="paired-header">
                  <strong>{pt.model_a_name} vs {pt.model_b_name}</strong>
                  <span className={`sig-pill ${pt.statistically_significant ? 'pill-sig' : 'pill-ns'}`}>
                    {pt.statistically_significant ? 'p < 0.05 (Significant)' : 'p ≥ 0.05 (Not Significant)'}
                  </span>
                </div>
                <div className="paired-body">
                  <div><strong>Metric:</strong> {pt.metric_name}</div>
                  <div><strong>Observed Difference (Δ):</strong> {pt.difference.toFixed(4)}</div>
                  <div><strong>95% CI on Δ:</strong> [{pt.ci_lower.toFixed(4)}, {pt.ci_upper.toFixed(4)}]</div>
                  <div><strong>p-value:</strong> {pt.p_value.toFixed(4)} ({pt.test_type})</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
