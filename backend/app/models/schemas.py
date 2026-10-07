from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(protected_namespaces=())

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str]

class SessionResponse(BaseModel):
    user: UserProfile
    csrf_token: str
    demo_mode: bool

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    task_type: str = Field(..., pattern="^(classification|regression)$")
    target_column: str = Field(default="label", max_length=64)
    cohort_columns: List[str] = Field(default_factory=list)

class DatasetItemCreate(BaseModel):
    item_key: str = Field(..., max_length=128)
    ground_truth: str = Field(..., max_length=128)
    cohorts: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    task_type: str
    target_column: str
    cohort_columns: List[str]
    item_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime

class ModelRunCreate(BaseModel):
    dataset_id: int
    name: str = Field(..., min_length=2, max_length=120)
    version: str = Field(default="1.0.0", max_length=32)
    architecture: str = Field(default="Transformer", max_length=120)
    description: Optional[str] = None

class PredictionItem(BaseModel):
    item_key: str
    predicted_label: str
    probability: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None

class PredictionBatchUpload(BaseModel):
    predictions: List[PredictionItem]

class ModelRunResponse(BaseModel):
    id: int
    dataset_id: int
    name: str
    version: str
    architecture: str
    description: Optional[str]
    prediction_count: int
    created_by: str
    created_at: datetime

class ConfidenceInterval(BaseModel):
    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    standard_error: float

class ModelMetrics(BaseModel):
    model_run_id: int
    model_name: str
    sample_size: int
    metrics: Dict[str, float]
    bootstrap_cis: Dict[str, ConfidenceInterval]

class PairedHypothesisResult(BaseModel):
    model_a_id: int
    model_a_name: str
    model_b_id: int
    model_b_name: str
    metric_name: str
    difference: float
    ci_lower: float
    ci_upper: float
    p_value: float
    statistically_significant: bool
    test_type: str
    winner_id: Optional[int] = None

class SliceDisparityResult(BaseModel):
    cohort_name: str
    cohort_value: str
    sample_size: int
    percentage_of_total: float
    metrics_by_model: Dict[str, Dict[str, float]]
    disparity_ratio: Optional[float] = None
    is_worst_slice: bool = False

class CalibrationBin(BaseModel):
    bin_index: int
    bin_center: float
    sample_count: int
    mean_predicted_prob: float
    empirical_accuracy: float

class ReliabilityDiagram(BaseModel):
    model_run_id: int
    model_name: str
    expected_calibration_error: float
    max_calibration_error: float
    brier_score: float
    bins: List[CalibrationBin]

class ArenaEvaluationRequest(BaseModel):
    dataset_id: int
    model_run_ids: List[int] = Field(..., min_length=1)
    resamples: int = Field(default=500, ge=50, le=2000)
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.99)
    cohort_slices: Optional[List[str]] = None

class ArenaEvaluationResponse(BaseModel):
    report_id: Optional[int] = None
    dataset_id: int
    dataset_name: str
    task_type: str
    models: List[ModelMetrics]
    paired_tests: List[PairedHypothesisResult]
    slice_breakdowns: List[SliceDisparityResult]
    calibration_diagrams: Optional[List[ReliabilityDiagram]] = None
    generated_at: datetime

class AdvisoryAuditRequest(BaseModel):
    dataset_id: int
    model_run_ids: List[int]
    focus_metric: Optional[str] = "accuracy"
    user_context: Optional[str] = None

class AdvisoryAuditResponse(BaseModel):
    status: str
    provider: str
    model: str
    analysis: str
    advisory_disclaimer: str
    grounded_evidence: Dict[str, Any]

class AuditLogEntry(BaseModel):
    id: int
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    created_at: datetime

class PaginatedAuditLogs(BaseModel):
    total: int
    items: List[AuditLogEntry]
