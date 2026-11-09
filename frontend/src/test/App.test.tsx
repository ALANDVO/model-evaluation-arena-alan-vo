import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Navbar } from '../components/Navbar';
import { MetricsTable } from '../components/MetricsTable';
import { SliceDisparityView } from '../components/SliceDisparityView';
import { CalibrationCurve } from '../components/CalibrationCurve';
import { EvaluationReportComparison } from '../components/EvaluationReportComparison';
import { AuthProvider } from '../context/AuthContext';
import { ModelMetrics, PairedHypothesisResult, ReliabilityDiagram, SliceDisparityResult, ArenaEvaluationResponse, Dataset } from '../types/api';

vi.mock('../api/client', () => ({
  api: {
    listReports: vi.fn(),
    getReportDetails: vi.fn(),
  }
}));

import { api } from '../api/client';

const mockDataset: Dataset = {
  id: 1,
  name: 'Test Benchmark',
  description: 'Test dataset',
  task_type: 'classification',
  target_column: 'label',
  cohort_columns: ['region', 'age_group'],
  item_count: 100,
  created_by: 'analyst',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

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
      macro_f1: {
        point_estimate: 0.91,
        ci_lower: 0.87,
        ci_upper: 0.94,
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
      macro_f1: {
        point_estimate: 0.80,
        ci_lower: 0.74,
        ci_upper: 0.85,
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

const mockSlices: SliceDisparityResult[] = [
  {
    cohort_name: 'region',
    cohort_value: 'North America',
    sample_size: 50,
    percentage_of_total: 50,
    metrics_by_model: { '1': { accuracy: 0.94 }, '2': { accuracy: 0.84 } },
    disparity_ratio: 0.89,
    is_worst_slice: false,
  },
  {
    cohort_name: 'region',
    cohort_value: 'APAC',
    sample_size: 50,
    percentage_of_total: 50,
    metrics_by_model: { '1': { accuracy: 0.72 }, '2': { accuracy: 0.78 } },
    disparity_ratio: 1.08,
    is_worst_slice: true,
  },
];

const mockReport1: ArenaEvaluationResponse = {
  report_id: 1,
  dataset_id: 1,
  dataset_name: 'Test Benchmark',
  task_type: 'classification',
  models: mockModels,
  paired_tests: mockPaired,
  slice_breakdowns: mockSlices,
  calibration_diagrams: [],
  generated_at: new Date().toISOString(),
};

const mockReportSummaries = [
  { id: 1, dataset_id: 1, title: 'Report 1', model_run_ids: [1, 2], created_by: 'analyst', created_at: new Date().toISOString() },
  { id: 2, dataset_id: 1, title: 'Report 2', model_run_ids: [1, 2], created_by: 'analyst', created_at: new Date().toISOString() },
];

describe('Frontend Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

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
    expect(screen.getByText((content) => content.includes('95% CI') && content.includes('0.8800') && content.includes('0.9500'))).toBeInTheDocument();
    expect(screen.getByText(/Significant/i)).toBeInTheDocument();
  });

  it('renders SliceDisparityView highlighting demographic disparity and worst slice', () => {
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

  it('renders EvaluationReportComparison with metrics, paired tests, and slice disparities', async () => {
    (api.listReports as any).mockResolvedValue(mockReportSummaries);
    (api.getReportDetails as any).mockResolvedValue(mockReport1);

    render(
      <AuthProvider>
        <EvaluationReportComparison
          datasets={[mockDataset]}
          selectedDataset={mockDataset}
          onSelectDataset={() => {}}
        />
      </AuthProvider>
    );

    // Wait for reports to load - initial state shows "Report Comparison"
    await waitFor(() => {
      expect(screen.getByText('Report Comparison')).toBeInTheDocument();
    });

    // Check that report list is rendered (checkboxes for selection)
    expect(screen.getByRole('checkbox', { name: /Report 1/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /Report 2/i })).toBeInTheDocument();

    // Select first report - this will trigger load
    const checkbox1 = screen.getByRole('checkbox', { name: /Report 1/i });
    checkbox1.click();

    await waitFor(() => {
      expect(screen.getByText('Comparison: 1 Reports')).toBeInTheDocument();
    });

    // Check metrics table renders - use getAllByText since Model Alpha appears in multiple places
    const modelAlphaElements = screen.getAllByText('Model Alpha');
    expect(modelAlphaElements.length).toBeGreaterThanOrEqual(1);
    const modelBetaElements = screen.getAllByText('Model Beta');
    expect(modelBetaElements.length).toBeGreaterThanOrEqual(1);
    const accuracyElements = screen.getAllByText('accuracy');
    expect(accuracyElements.length).toBeGreaterThanOrEqual(1);
    const macroF1Elements = screen.getAllByText('macro_f1');
    expect(macroF1Elements.length).toBeGreaterThanOrEqual(1);

    // Check paired tests section
    expect(screen.getByText('Paired Tests')).toBeInTheDocument();
    expect(screen.getByText('Model Alpha vs Model Beta')).toBeInTheDocument();
    expect(screen.getByText('Significant')).toBeInTheDocument();

    // Check slice disparities section
    expect(screen.getByText('Slice Disparities')).toBeInTheDocument();
    expect(screen.getByText('North America')).toBeInTheDocument();
    expect(screen.getByText('APAC')).toBeInTheDocument();
    expect(screen.getByText('Worst')).toBeInTheDocument();

    // Check export buttons
    expect(screen.getByRole('button', { name: /Export JSON/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Export CSV/i })).toBeInTheDocument();
  });
});
