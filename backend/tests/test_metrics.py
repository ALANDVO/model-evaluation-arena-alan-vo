import pytest
from app.services.eval_metrics import (
    compute_classification_metrics,
    compute_calibration_curve,
    compute_regression_metrics,
)

def test_classification_metrics_perfect():
    y_true = ["cat", "dog", "cat", "dog"]
    y_pred = ["cat", "dog", "cat", "dog"]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_precision"] == 1.0
    assert metrics["macro_recall"] == 1.0
    assert metrics["macro_f1"] == 1.0

def test_classification_metrics_imperfect():
    y_true = ["1", "1", "0", "0"]
    y_pred = ["1", "0", "0", "0"]
    probs = [0.9, 0.4, 0.1, 0.2]
    metrics = compute_classification_metrics(y_true, y_pred, probabilities=probs)
    assert metrics["accuracy"] == 0.75
    assert "brier_score" in metrics
    assert "log_loss" in metrics
    assert "roc_auc" in metrics
    assert metrics["roc_auc"] > 0.5

def test_calibration_curve():
    y_true_bin = [1, 1, 0, 0, 1, 0, 1, 0, 1, 0]
    probs = [0.95, 0.85, 0.15, 0.25, 0.75, 0.35, 0.65, 0.45, 0.80, 0.10]
    ece, mce, bins = compute_calibration_curve(y_true_bin, probs, num_bins=5)
    assert 0.0 <= ece <= 1.0
    assert 0.0 <= mce <= 1.0
    assert len(bins) == 5
    assert all("empirical_accuracy" in b for b in bins)

def test_regression_metrics():
    y_true = [10.0, 20.0, 30.0, 40.0]
    y_pred = [11.0, 19.0, 31.0, 39.0]
    metrics = compute_regression_metrics(y_true, y_pred)
    assert metrics["mse"] == 1.0
    assert metrics["rmse"] == 1.0
    assert metrics["mae"] == 1.0
    assert metrics["r2"] > 0.95
    assert metrics["pearson_r"] > 0.95

def test_empty_metrics():
    assert compute_classification_metrics([], []) == {}
    assert compute_regression_metrics([], []) == {}
