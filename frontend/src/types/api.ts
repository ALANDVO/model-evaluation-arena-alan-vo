export type TaskType = 'classification' | 'regression';

export interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  roles: string[];
}

export interface SessionInfo {
  authenticated: boolean;
  user: UserProfile | null;
  csrf_token: string;
  demo_mode: boolean;
  environment: string;
}

export interface DatasetItem {
  id: number;
  item_key: string;
  ground_truth: string;
  cohorts: Record<string, string>;
  metadata: Record<string, any>;
}

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  task_type: TaskType;
  target_column: string;
  cohort_columns: string[];
  item_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  sample_items?: DatasetItem[];
}

export interface ModelRun {
  id: number;
  dataset_id: number;
  name: string;
  version: string;
  architecture: string;
  description?: string;
  prediction_count: number;
  created_by: string;
  created_at: string;
}

export interface ConfidenceInterval {
  point_estimate: number;
  ci_lower: number;
  ci_upper: number;
  confidence_level: number;
  standard_error: number;
}

export interface ModelMetrics {
  model_run_id: number;
  model_name: string;
  sample_size: number;
  metrics: Record<string, number>;
  bootstrap_cis: Record<string, ConfidenceInterval>;
}

export interface PairedHypothesisResult {
  model_a_id: number;
  model_a_name: string;
  model_b_id: number;
  model_b_name: string;
  metric_name: string;
  difference: number;
  ci_lower: number;
  ci_upper: number;
  p_value: number;
  statistically_significant: boolean;
  test_type: string;
  winner_id?: number | null;
}

export interface SliceDisparityResult {
  cohort_name: string;
  cohort_value: string;
  sample_size: number;
  percentage_of_total: number;
  metrics_by_model: Record<string, Record<string, number>>;
  disparity_ratio?: number | null;
  is_worst_slice: boolean;
}

export interface CalibrationBin {
  bin_index: number;
  bin_center: number;
  sample_count: number;
  mean_predicted_prob: number;
  empirical_accuracy: number;
}

export interface ReliabilityDiagram {
  model_run_id: number;
  model_name: string;
  expected_calibration_error: number;
  max_calibration_error: number;
  brier_score: number;
  bins: CalibrationBin[];
}

export interface ArenaEvaluationResponse {
  report_id?: number;
  dataset_id: number;
  dataset_name: string;
  task_type: TaskType;
  models: ModelMetrics[];
  paired_tests: PairedHypothesisResult[];
  slice_breakdowns: SliceDisparityResult[];
  calibration_diagrams?: ReliabilityDiagram[];
  generated_at: string;
}

export interface AdvisoryAuditResponse {
  status: string;
  provider: string;
  model: string;
  analysis: string;
  advisory_disclaimer: string;
  grounded_evidence: Record<string, any>;
}

export interface AuditLogEntry {
  id: number;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  created_at: string;
}
