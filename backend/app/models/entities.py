import datetime
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    task_type = Column(String(32), nullable=False)  # "classification" or "regression"
    target_column = Column(String(64), nullable=False, default="label")
    cohort_columns = Column(Text, nullable=False, default="[]")  # JSON array of cohort feature names
    created_by = Column(String(120), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    items = relationship("DatasetItem", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("ModelRun", back_populates="dataset", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationReport", back_populates="dataset", cascade="all, delete-orphan")

class DatasetItem(Base):
    __tablename__ = "dataset_items"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    item_key = Column(String(128), nullable=False, index=True)
    ground_truth = Column(String(128), nullable=False)  # String representation: '0'/'1', category name, or float '3.14'
    cohorts_json = Column(Text, nullable=False, default="{}")  # JSON map of feature -> cohort_val
    metadata_json = Column(Text, nullable=False, default="{}")

    dataset = relationship("Dataset", back_populates="items")

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
    version = Column(String(32), nullable=False, default="1.0.0")
    architecture = Column(String(120), nullable=False, default="unknown")
    description = Column(Text, nullable=True)
    created_by = Column(String(120), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset = relationship("Dataset", back_populates="runs")
    predictions = relationship("Prediction", back_populates="model_run", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    item_key = Column(String(128), nullable=False, index=True)
    predicted_label = Column(String(128), nullable=False)  # Predicted class or float value as str
    probability = Column(Float, nullable=True)  # Confidence or positive class probability
    probabilities_json = Column(Text, nullable=True)  # Full probability distribution JSON if multi-class

    model_run = relationship("ModelRun", back_populates="predictions")

class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    model_run_ids = Column(Text, nullable=False)  # JSON array of int IDs
    metrics_summary = Column(Text, nullable=False)  # JSON map of model_id -> metrics
    bootstrap_results = Column(Text, nullable=False)  # JSON map of model_id -> metric -> CI
    slice_disparities = Column(Text, nullable=False)  # JSON array of slice disparity breakdowns
    paired_comparisons = Column(Text, nullable=False)  # JSON paired hypothesis tests
    advisory_notes = Column(Text, nullable=True)
    created_by = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset = relationship("Dataset", back_populates="evaluations")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(120), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=True)
    details = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
