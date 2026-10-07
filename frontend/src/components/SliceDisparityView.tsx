import React from 'react';
import { ModelMetrics, SliceDisparityResult } from '../types/api';

interface SliceDisparityViewProps {
  slices: SliceDisparityResult[];
  models: ModelMetrics[];
}

export const SliceDisparityView: React.FC<SliceDisparityViewProps> = ({ slices, models }) => {
  if (slices.length === 0) {
    return (
      <div className="card">
        <div className="empty-notice">
          No cohort features identified for this benchmark. Add cohort metadata during dataset ingestion to evaluate demographic slice disparities.
        </div>
      </div>
    );
  }

  const worstSlice = slices.find((s) => s.is_worst_slice);

  return (
    <div className="card slice-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Cohort Slice & Demographic Disparity Analysis</h2>
          <p className="card-subtitle">Granular evaluation across slice attributes with disparity ratios</p>
        </div>
      </div>

      {worstSlice && (
        <div className="alert-banner warning-banner">
          <span className="banner-icon">⚠️</span>
          <div>
            <strong>Vulnerability Alert (Worst-Performing Cohort):</strong> Slice{' '}
            <code>{worstSlice.cohort_name} = {worstSlice.cohort_value}</code> exhibits the lowest composite score.
            Sample size: {worstSlice.sample_size} ({worstSlice.percentage_of_total}% of dataset).
            {worstSlice.disparity_ratio && (
              <span> Disparity ratio across models: <strong>{(worstSlice.disparity_ratio * 100).toFixed(1)}%</strong>.</span>
            )}
          </div>
        </div>
      )}

      <div className="table-responsive">
        <table className="arena-table slice-table">
          <thead>
            <tr>
              <th>Cohort Feature</th>
              <th>Slice Value</th>
              <th>Sample Count</th>
              <th>% of Total</th>
              <th>Disparity Ratio</th>
              {models.map((m) => (
                <th key={m.model_run_id}>{m.model_name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slices.map((s, idx) => {
              const disp = s.disparity_ratio !== null && s.disparity_ratio !== undefined ? s.disparity_ratio : 1.0;
              const isLow = disp < 0.85;

              return (
                <tr key={idx} className={s.is_worst_slice ? 'worst-slice-row' : ''}>
                  <td><code>{s.cohort_name}</code></td>
                  <td>
                    <strong>{s.cohort_value}</strong>
                    {s.is_worst_slice && <span className="worst-badge">Worst Slice</span>}
                  </td>
                  <td>{s.sample_size}</td>
                  <td>{s.percentage_of_total}%</td>
                  <td>
                    <div className="disparity-bar-wrap">
                      <div
                        className={`disparity-bar ${isLow ? 'bar-low' : 'bar-good'}`}
                        style={{ width: `${Math.min(100, Math.max(10, disp * 100))}%` }}
                      />
                      <span className="disparity-text">{(disp * 100).toFixed(1)}%</span>
                    </div>
                  </td>
                  {models.map((m) => {
                    const modelMetrics = s.metrics_by_model[String(m.model_run_id)] || {};
                    const val = modelMetrics['accuracy'] ?? modelMetrics['rmse'] ?? Object.values(modelMetrics)[0] ?? 0;
                    return (
                      <td key={m.model_run_id} className="slice-metric-cell">
                        {typeof val === 'number' ? val.toFixed(4) : '-'}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
