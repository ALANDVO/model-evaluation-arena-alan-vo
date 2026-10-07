import pytest
from app.services.bootstrap import (
    bootstrap_confidence_interval,
    bootstrap_model_metrics,
    paired_bootstrap_comparison,
)

def test_bootstrap_confidence_interval():
    data = [10.0, 11.0, 12.0, 10.5, 9.5, 10.2, 11.8]
    lower, upper, se = bootstrap_confidence_interval(data, confidence_level=0.95)
    assert lower <= upper
    assert se > 0

def test_bootstrap_model_metrics_classification():
    y_true = ["1"] * 50 + ["0"] * 50
    y_pred = ["1"] * 45 + ["0"] * 5 + ["1"] * 5 + ["0"] * 45
    point_m, ci_m = bootstrap_model_metrics(
        y_true=y_true,
        y_pred=y_pred,
        task_type="classification",
        resamples=100,
        seed=123,
    )
    assert point_m["accuracy"] == 0.90
    assert "accuracy" in ci_m
    acc_ci = ci_m["accuracy"]
    assert acc_ci["ci_lower"] <= 0.90 <= acc_ci["ci_upper"]
    assert acc_ci["standard_error"] > 0

def test_paired_bootstrap_comparison_significant():
    y_true = ["1"] * 100
    pred_a = ["1"] * 95 + ["0"] * 5  # 95% acc
    pred_b = ["1"] * 60 + ["0"] * 40  # 60% acc
    comp = paired_bootstrap_comparison(
        y_true=y_true,
        pred_a=pred_a,
        pred_b=pred_b,
        task_type="classification",
        metric_name="accuracy",
        resamples=150,
    )
    assert comp["difference"] == 0.35
    assert comp["ci_lower"] > 0
    assert comp["statistically_significant"] is True
