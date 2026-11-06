import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../api/client';
import { ArenaEvaluationResponse, Dataset } from '../types/api';

type ReportSummary = {
  id: number;
  dataset_id: number;
  title: string;
  model_run_ids: number[];
  created_by: string;
  created_at: string;
};

export const EvaluationReportComparison: React.FC<{
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  onSelectDataset: (d: Dataset) => void;
}> = ({ datasets, selectedDataset, onSelectDataset }) => {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [sel, setSel] = useState<number[]>([]);
  const [loaded, setLoaded] = useState<ArenaEvaluationResponse[]>([]);
  const [loading, setLoading] = useState<Set<number>>(new Set());
  const [err, setErr] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);

  const fetchReports = async () => {
    setListLoading(true);
    try {
      const data = await api.listReports(selectedDataset?.id);
      setReports(data);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [selectedDataset]);

  const toggleSel = (id: number) => {
    setSel((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const clear = () => {
    setSel([]);
    setLoaded([]);
    setErr(null);
  };

  const load = async (id: number) => {
    setLoading((prev) => {
      const n = new Set(prev);
      n.add(id);
      return n;
    });
    try {
      const data = await api.getReportDetails(id);
      setLoaded((prev) => (prev.some((r) => r.report_id === id) ? prev : [...prev, data]));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading((prev) => {
        const n = new Set(prev);
        n.delete(id);
        return n;
      });
    }
  };

  const loadSel = async () => {
    for (const id of sel) {
      if (!loaded.some((r) => r.report_id === id) && !loading.has(id)) {
        await load(id);
      }
    }
  };

  useEffect(() => {
    loadSel();
  }, [sel]);

  const metrics = useMemo(
    () => [...new Set(loaded.flatMap((r) => r.models.flatMap((m) => Object.keys(m.metrics))))],
    [loaded]
  );

  const handleExport = async (format: 'json' | 'csv') => {
    if (!loaded.length) return;
    setExporting(format);
    try {
      if (format === 'json') {
        const exportData = {
          exported_at: new Date().toISOString(),
          report_count: loaded.length,
          reports: loaded.map((r) => ({
            report_id: r.report_id,
            dataset_id: r.dataset_id,
            dataset_name: r.dataset_name,
            task_type: r.task_type,
            generated_at: r.generated_at,
            models: r.models.map((m) => ({
              model_run_id: m.model_run_id,
              model_name: m.model_name,
              n: m.sample_size,
              metrics: m.metrics,
              bootstrap_ci: m.bootstrap_cis,
            })),
            paired_tests: r.paired_tests,
            slice_breakdowns: r.slice_breakdowns,
            calibration_diagrams: r.calibration_diagrams,
          })),
        };
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comparison_${loaded.map((r) => r.report_id).join('_')}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // CSV export - flatten the comparison data
        const rows: string[][] = [
          [
            'report_id',
            'dataset_id',
            'dataset_name',
            'task_type',
            'model_run_id',
            'model_name',
            'n',
            'metric_name',
            'metric_value',
            'ci_lower',
            'ci_upper',
            'ci_std_err',
          ],
        ];
        for (const r of loaded) {
          for (const m of r.models) {
            for (const [metricName, metricValue] of Object.entries(m.metrics)) {
              const ci = m.bootstrap_cis?.[metricName];
              rows.push([
                String(r.report_id),
                String(r.dataset_id),
                r.dataset_name,
                r.task_type,
                String(m.model_run_id),
                m.model_name,
                String(m.sample_size),
                metricName,
                String(metricValue),
                ci?.ci_lower?.toString() ?? '',
                ci?.ci_upper?.toString() ?? '',
                ci?.standard_error?.toString() ?? '',
              ]);
            }
          }
        }
        // Add paired tests
        rows.push([]);
        rows.push(['paired_tests']);
        rows.push([
          'report_id',
          'model_a_name',
          'model_b_name',
          'metric_name',
          'difference',
          'p_value',
          'statistically_significant',
          'test_type',
        ]);
        for (const r of loaded) {
          for (const pt of r.paired_tests) {
            rows.push([
              String(r.report_id),
              pt.model_a_name,
              pt.model_b_name,
              pt.metric_name,
              String(pt.difference),
              String(pt.p_value),
              String(pt.statistically_significant),
              pt.test_type,
            ]);
          }
        }
        // Add slice breakdowns
        rows.push([]);
        rows.push(['slice_breakdowns']);
        rows.push([
          'report_id',
          'cohort_name',
          'cohort_value',
          'sample_size',
          'percentage_of_total',
          'is_worst_slice',
          'disparity_ratio',
          'model_run_id',
          'model_name',
          'metric_name',
          'metric_value',
        ]);
        for (const r of loaded) {
          for (const s of r.slice_breakdowns) {
            for (const m of r.models) {
              const mm = s.metrics_by_model?.[m.model_run_id];
              if (mm) {
                for (const [metricName, metricValue] of Object.entries(mm)) {
                  rows.push([
                    String(r.report_id),
                    s.cohort_name,
                    s.cohort_value,
                    String(s.sample_size),
                    String(s.percentage_of_total),
                    String(s.is_worst_slice),
                    String(s.disparity_ratio ?? ''),
                    String(m.model_run_id),
                    m.model_name,
                    metricName,
                    String(metricValue),
                  ]);
                }
              }
            }
          }
        }
        const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `comparison_${loaded.map((r) => r.report_id).join('_')}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e: any) {
      setErr(`Export failed: ${e.message}`);
    } finally {
      setExporting(null);
    }
  };

  if (!loaded.length && !sel.length) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Report Comparison</h2>
          <p className="card-subtitle">Select reports to compare metrics, tests, slice disparities</p>
        </div>
        <div className="reports-selector">
          {listLoading ? (
            <div className="loading-spinner">Loading...</div>
          ) : (
            <>
              <div className="filter-row">
                <label>
                  Filter:
                  <select
                    value={selectedDataset?.id ?? ''}
                    onChange={(e) => onSelectDataset(datasets.find((d) => d.id === Number(e.target.value))!)}
                  >
                    <option value="">All Datasets</option>
                    {datasets.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="reports-list">
                {reports.length === 0 ? (
                  <p className="empty-notice">No evaluation reports found.</p>
                ) : (
                  reports.map((r) => (
                    <label key={r.id} className="report-row">
                      <input
                        type="checkbox"
                        checked={sel.includes(r.id)}
                        onChange={() => toggleSel(r.id)}
                      />
                      <span>#{r.id} - {r.title} (Dataset {r.dataset_id})</span>
                      <small>{new Date(r.created_at).toLocaleString()}</small>
                    </label>
                  ))
                )}
              </div>
              {sel.length > 0 && (
                <button className="primary-btn" onClick={loadSel} disabled={loading.size > 0}>
                  {loading.size > 0 ? 'Loading...' : `Load ${sel.length} Report(s)`}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="comparison-view">
      <div className="comparison-header">
        <h2 className="card-title">Comparison: {loaded.length} Reports</h2>
        <div className="header-actions">
          <button className="secondary-btn" onClick={clear}>
            Clear
          </button>
          <div className="export-buttons">
            <button
              className="secondary-btn"
              onClick={() => handleExport('json')}
              disabled={exporting !== null}
            >
              {exporting === 'json' ? 'Exporting JSON...' : 'Export JSON'}
            </button>
            <button
              className="secondary-btn"
              onClick={() => handleExport('csv')}
              disabled={exporting !== null}
            >
              {exporting === 'csv' ? 'Exporting CSV...' : 'Export CSV'}
            </button>
          </div>
        </div>
      </div>
      {err && <div className="alert-banner error-banner">{err}</div>}
      <div className="card">
        <div className="card-header">
          <h3 className="section-title">Metrics &amp; 95% CI</h3>
        </div>
        <div className="table-responsive">
          <table className="arena-table">
            <thead>
              <tr>
                <th>Report</th>
                <th>Dataset</th>
                <th>Task</th>
                <th>Model</th>
                <th>N</th>
                {metrics.map((m) => (
                  <th key={m}>
                    <div className="metric-col-header">
                      <span className="metric-name">{m}</span>
                      <span className="ci-label">95% CI</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loaded.flatMap((r) =>
                r.models.map((m) => (
                  <tr key={`${r.report_id}-${m.model_run_id}`}>
                    <td>#{r.report_id}</td>
                    <td>{r.dataset_name}</td>
                    <td>{r.task_type}</td>
                    <td>{m.model_name}</td>
                    <td>{m.sample_size}</td>
                    {metrics.map((metric) => (
                      <td key={metric}>
                        {m.metrics[metric] !== undefined ? (
                          <>
                            <span className="metric-value">{Number(m.metrics[metric]).toFixed(4)}</span>
                            {m.bootstrap_cis?.[metric] && (
                              <span className="ci-badge">
                                [{Number(m.bootstrap_cis[metric].ci_lower).toFixed(4)}, {Number(m.bootstrap_cis[metric].ci_upper).toFixed(4)}]
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
              {!loaded.length && (
                <tr>
                  <td colSpan={100} className="empty-notice">
                    No reports loaded
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      {loaded.some((r) => r.paired_tests.length) && (
        <div className="card">
          <div className="card-header">
            <h3 className="section-title">Paired Tests</h3>
          </div>
          <div className="paired-tests-comparison-grid">
            {loaded.map((r) => (
              <div key={r.report_id} className="report-section">
                <h4 className="report-section-title">#{r.report_id}: {r.dataset_name}</h4>
                <div className="paired-grid">
                  {r.paired_tests.map((pt, i) => (
                    <div key={i} className={`paired-card ${pt.statistically_significant ? 'sig-card' : ''}`}>
                      <div className="paired-header">
                        <strong>{pt.model_a_name} vs {pt.model_b_name}</strong>
                        <span className={`sig-pill ${pt.statistically_significant ? 'pill-sig' : 'pill-ns'}`}>
                          {pt.statistically_significant ? 'Significant' : 'Not Significant'}
                        </span>
                      </div>
                      <div className="paired-detail">
                        Metric: <code>{pt.metric_name}</code> | Δ = {pt.difference.toFixed(4)} | p = {pt.p_value.toFixed(4)} ({pt.test_type})
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {loaded.some((r) => r.slice_breakdowns.length) && (
        <div className="card">
          <div className="card-header">
            <h3 className="section-title">Slice Disparities</h3>
          </div>
          <div className="slice-comparison-grid">
            {loaded.map((r) => (
              <div key={r.report_id} className="report-section">
                <h4 className="report-section-title">#{r.report_id}: {r.dataset_name}</h4>
                {r.slice_breakdowns.map((s) => (
                  <div key={`${r.report_id}-${s.cohort_name}-${s.cohort_value}`} className="slice-entry">
                    <div className="slice-header">
                      <code>{s.cohort_name}</code>=<strong>{s.cohort_value}</strong>
                      {s.is_worst_slice && <span className="worst-badge">Worst</span>}
                      <span className="sample-info">N={s.sample_size} ({s.percentage_of_total}%)</span>
                    </div>
                    <div className="slice-metrics">
                      {r.models.map((m) => {
                        const mm = s.metrics_by_model?.[m.model_run_id];
                        if (!mm) return null;
                        return (
                          <div key={m.model_run_id} className="model-slice-metrics">
                            <strong>{m.model_name}</strong>
                            {Object.entries(mm).map(([metric, val]) => (
                              <span key={metric} className="slice-metric">
                                {metric}: {Number(val).toFixed(4)}
                              </span>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
