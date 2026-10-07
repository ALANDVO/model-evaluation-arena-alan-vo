import React, { useState } from 'react';
import { ReliabilityDiagram } from '../types/api';

interface Props { diagrams: ReliabilityDiagram[]; }

export const CalibrationCurve: React.FC<Props> = ({ diagrams }) => {
  if (!diagrams || diagrams.length === 0) return null;
  const [idx, setIdx] = useState(0);
  const cur = diagrams[idx] || diagrams[0];

  const sz = 300, pad = 40, pSz = sz - pad * 2;
  const toX = (v: number) => pad + v * pSz, toY = (v: number) => pad + (1 - v) * pSz;

  return (
    <div className="card calibration-card">
      <div className="card-header flex-between">
        <div>
          <h2 className="card-title">Reliability & Calibration Curve</h2>
          <p className="card-subtitle">Empirical accuracy vs confidence bins (10 quantiles)</p>
        </div>
        {diagrams.length > 1 && (
          <select value={idx} onChange={(e) => setIdx(Number(e.target.value))} className="input-select">
            {diagrams.map((d, i) => <option key={d.model_run_id} value={i}>{d.model_name}</option>)}
          </select>
        )}
      </div>

      <div className="calibration-stats-row">
        <div className="stat-pill"><span className="stat-label">ECE</span><span className="stat-val">{(cur.expected_calibration_error * 100).toFixed(2)}%</span></div>
        <div className="stat-pill"><span className="stat-label">MCE</span><span className="stat-val">{(cur.max_calibration_error * 100).toFixed(2)}%</span></div>
        <div className="stat-pill"><span className="stat-label">Brier</span><span className="stat-val">{cur.brier_score.toFixed(4)}</span></div>
      </div>

      <div className="svg-container flex-center">
        <svg viewBox={`0 0 ${sz} ${sz}`} className="calibration-svg" width={sz} height={sz}>
          {[0, 0.5, 1.0].map((t) => (
            <g key={t}>
              <line x1={toX(t)} y1={toY(0)} x2={toX(t)} y2={toY(1)} stroke="#334155" />
              <line x1={toX(0)} y1={toY(t)} x2={toX(1)} y2={toY(t)} stroke="#334155" />
              <text x={toX(t)} y={toY(0) + 12} fontSize="9" textAnchor="middle" fill="#94a3b8">{t.toFixed(1)}</text>
              <text x={toX(0) - 6} y={toY(t) + 3} fontSize="9" textAnchor="end" fill="#94a3b8">{t.toFixed(1)}</text>
            </g>
          ))}
          <line x1={toX(0)} y1={toY(0)} x2={toX(1)} y2={toY(1)} stroke="#94a3b8" strokeDasharray="3 3" strokeWidth="1.5" />
          {cur.bins.map((b) => {
            if (b.sample_count === 0) return null;
            const bw = (pSz / 10) * 0.7, xc = toX(b.bin_center), ya = toY(b.empirical_accuracy), yb = toY(0);
            return (
              <g key={b.bin_index}>
                <rect x={xc - bw / 2} y={ya} width={bw} height={Math.max(yb - ya, 0)} fill="#3b82f6" opacity="0.3" rx="2" />
                <circle cx={xc} cy={ya} r="3.5" fill="#2563eb" />
              </g>
            );
          })}
          <text x={sz / 2} y={sz - 4} textAnchor="middle" fontSize="9" fill="#94a3b8">Confidence</text>
          <text x={-sz / 2} y={10} textAnchor="middle" fontSize="9" fill="#94a3b8" transform="rotate(-90)">Accuracy</text>
        </svg>
      </div>
    </div>
  );
};
