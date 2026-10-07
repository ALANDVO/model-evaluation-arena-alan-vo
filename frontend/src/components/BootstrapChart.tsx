import React, { useState } from 'react';
import { ModelMetrics } from '../types/api';

interface Props { models: ModelMetrics[]; }

export const BootstrapChart: React.FC<Props> = ({ models }) => {
  if (models.length === 0) return null;
  const metrics = Object.keys(models[0].metrics);
  const [selected, setSelected] = useState(metrics.includes('accuracy') ? 'accuracy' : metrics[0] || 'rmse');

  let minVal = Infinity, maxVal = -Infinity;
  models.forEach((m) => {
    const ci = m.bootstrap_cis[selected];
    const lo = ci ? ci.ci_lower : (m.metrics[selected] ?? 0);
    const hi = ci ? ci.ci_upper : (m.metrics[selected] ?? 0);
    if (lo < minVal) minVal = lo;
    if (hi > maxVal) maxVal = hi;
  });
  if (minVal === Infinity) { minVal = 0.0; maxVal = 1.0; }

  const span = (maxVal - minVal) || 0.1;
  const pMin = Math.max(0, minVal - span * 0.15);
  const pMax = maxVal + span * 0.15;
  const pSpan = pMax - pMin;

  const w = 620, rowH = 50, topP = 30, botP = 30, leftP = 160, rightP = 50;
  const chartW = w - leftP - rightP;
  const h = topP + models.length * rowH + botP;
  const scaleX = (v: number) => leftP + ((v - pMin) / pSpan) * chartW;
  const colors = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

  return (
    <div className="card chart-card">
      <div className="card-header flex-between">
        <div>
          <h2 className="card-title">Bootstrap Distribution Forest Plot</h2>
          <p className="card-subtitle">Empirical point estimates with 95% confidence interval bounds</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <label htmlFor="forest-metric-select" style={{ fontSize: '0.85rem' }}>Metric:</label>
          <select id="forest-metric-select" value={selected} onChange={(e) => setSelected(e.target.value)} className="input-select">
            {metrics.map((k) => <option key={k} value={k}>{k}</option>)}
          </select>
        </div>
      </div>

      <div className="svg-container">
        <svg viewBox={`0 0 ${w} ${h}`} className="forest-svg" width="100%" height={h}>
          {[0, 0.5, 1.0].map((frac, idx) => {
            const tv = pMin + frac * pSpan;
            const xp = scaleX(tv);
            return (
              <g key={idx}>
                <line x1={xp} y1={topP - 5} x2={xp} y2={h - botP + 5} stroke="#334155" strokeDasharray="3 3" />
                <text x={xp} y={h - botP + 18} textAnchor="middle" fontSize="10" fill="#94a3b8">{tv.toFixed(3)}</text>
              </g>
            );
          })}
          {models.map((m, idx) => {
            const y = topP + idx * rowH + rowH / 2;
            const c = colors[idx % colors.length];
            const ci = m.bootstrap_cis[selected];
            const pt = m.metrics[selected] ?? 0;
            const px = scaleX(pt), lx = ci ? scaleX(ci.ci_lower) : px, rx = ci ? scaleX(ci.ci_upper) : px;

            return (
              <g key={m.model_run_id}>
                <text x={leftP - 12} y={y + 4} textAnchor="end" fontSize="12" fontWeight="600" fill="#f8fafc">
                  {m.model_name.length > 18 ? m.model_name.substring(0, 16) + '..' : m.model_name}
                </text>
                <line x1={lx} y1={y} x2={rx} y2={y} stroke={c} strokeWidth="3" strokeLinecap="round" />
                <line x1={lx} y1={y - 5} x2={lx} y2={y + 5} stroke={c} strokeWidth="2" />
                <line x1={rx} y1={y - 5} x2={rx} y2={y + 5} stroke={c} strokeWidth="2" />
                <circle cx={px} cy={y} r="5" fill={c} stroke="#0f172a" strokeWidth="1.5" />
                <text x={rx + 6} y={y + 3} fontSize="10" fill="#94a3b8">{pt.toFixed(3)}</text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
