import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Navbar } from '../components/Navbar';
import { MetricsTable } from '../components/MetricsTable';
import { SliceDisparityView } from '../components/SliceDisparityView';
import { CalibrationCurve } from '../components/CalibrationCurve';
import { AuthProvider } from '../context/AuthContext';
import { ModelMetrics, PairedHypothesisResult, ReliabilityDiagram, SliceDisparityResult } from '../types/api';

describe('Frontend Component Tests', () => {
  it('renders Navbar with title, author branding, and navigation buttons', () => {
    render(
      <AuthProvider>
        <Navbar activeTab="arena" setActiveTab={() => {}} />
      </AuthProvider>
    );

    expect(screen.getByText('Model Evaluation Arena')).toBeInTheDocument();
    expect(screen.getByText(/Alan Vo/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Arena Benchmark/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cohort Slices/i })).toBeInTheDocument();
  });

  it('renders MetricsTable with comparative bootstrap confidence intervals and leaders', () => {
    const mockModels: ModelMetrics[] = [
      {
        model_run_id: 1,
        model_name: 'Model Alpha',
        sample_size: 100,
        metrics: { accuracy: 0.92, macro_f1: 0.91 },
        bootstrap_cis: {
          accuracy: {
            point_estimate: 0.92,
            ci_lower: 0.88,
            ci_upper: 0.95,
            confidence_level: 0.95,
            standard_error: 0.018,
          },
        },
      },
      {
        model_run_id: 2,
        model_name: 'Model Beta',
        sample_size: 100,
        metrics: { accuracy: 0.81, macro_f1: 0.80 },
        bootstrap_cis: {
          accuracy: {
            point_estimate: 0.81,
            ci_lower: 0.75,
            ci_upper: 0.86,
            confidence_level: 0.95,
            standard_error: 0.028,
          },
        },
      },
    ];

    const mockPaired: PairedHypothesisResult[] = [
      {
        model_a_id: 1,
        model_a_name: 'Model Alpha',
        model_b_id: 2,
        model_b_name: 'Model Beta',
        metric_name: 'accuracy',
        difference: 0.11,
        ci_lower: 0.05,
        ci_upper: 0.17,
        p_value: 0.002,
        statistically_significant: true,
        test_type: 'McNemar test',
        winner_id: 1,
      },
    ];

    render(
      <MetricsTable
        taskType="classification"
        models={mockModels}
        pairedTests={mockPaired}
      />
    );

    expect(screen.getByText('Model Alpha')).toBeInTheDocument();
    expect(screen.getByText('Model Beta')).toBeInTheDocument();
    expect(screen.getAllByText(/Leader/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/95% CI: \[0.8800, 0.9500\]/i)).toBeInTheDocument();
    expect(screen.getByText(/Significant/i)).toBeInTheDocument();
  });

  it('renders SliceDisparityView highlighting demographic disparity and worst slice', () => {
    const mockSlices: SliceDisparityResult[] = [
      {
        cohort_name: 'region',
        cohort_value: 'North America',
        sample_size: 50,
        percentage_of_total: 50,
        metrics_by_model: { '1': { accuracy: 0.94 } },
        disparity_ratio: 0.94,
        is_worst_slice: false,
      },
      {
        cohort_name: 'region',
        cohort_value: 'APAC',
        sample_size: 50,
        percentage_of_total: 50,
        metrics_by_model: { '1': { accuracy: 0.72 } },
        disparity_ratio: 0.76,
        is_worst_slice: true,
      },
    ];

    const mockModels: ModelMetrics[] = [
      {
        model_run_id: 1,
        model_name: 'Model Alpha',
        sample_size: 100,
        metrics: { accuracy: 0.83 },
        bootstrap_cis: {},
      },
    ];

    render(<SliceDisparityView slices={mockSlices} models={mockModels} />);

    expect(screen.getByText('North America')).toBeInTheDocument();
    expect(screen.getByText('APAC')).toBeInTheDocument();
    expect(screen.getByText(/Worst-Performing Cohort/i)).toBeInTheDocument();
  });

  it('renders CalibrationCurve showing Expected Calibration Error and Brier score', () => {
    const mockDiagrams: ReliabilityDiagram[] = [
      {
        model_run_id: 1,
        model_name: 'Model Alpha',
        expected_calibration_error: 0.045,
        max_calibration_error: 0.082,
        brier_score: 0.091,
        bins: [
          {
            bin_index: 0,
            bin_center: 0.1,
            sample_count: 20,
            mean_predicted_prob: 0.12,
            empirical_accuracy: 0.10,
          },
        ],
      },
    ];

    render(<CalibrationCurve diagrams={mockDiagrams} />);

    expect(screen.getByText('4.50%')).toBeInTheDocument();
    expect(screen.getByText('8.20%')).toBeInTheDocument();
    expect(screen.getByText('0.0910')).toBeInTheDocument();
  });
});
