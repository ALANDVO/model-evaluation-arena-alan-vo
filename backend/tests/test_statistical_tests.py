import pytest
from app.services.statistical_tests import (
    mcnemar_test,
    paired_t_test,
    wilcoxon_signed_rank_test,
    compare_model_runs_statistical,
)

def test_mcnemar_test_discordant():
    y_true = ["1"] * 50
    pred_a = ["1"] * 45 + ["0"] * 5
    pred_b = ["1"] * 25 + ["0"] * 25
    res = mcnemar_test(y_true, pred_a, pred_b)
    assert res["b"] == 20  # A correct, B incorrect
    assert res["c"] == 0   # A incorrect, B correct
    assert res["statistic"] > 10
    assert res["p_value"] < 0.01

def test_paired_t_test():
    diffs = [2.0, 2.5, 1.8, 2.2, 2.1, 1.9, 2.4, 2.0]
    res = paired_t_test(diffs)
    assert res["statistic"] > 5
    assert res["p_value"] < 0.01

def test_wilcoxon_signed_rank_test_significant():
    # Model A consistently lower error than Model B
    diffs = [-1.0, -1.2, -0.8, -1.1, -0.9, -1.3, -0.7, -1.0, -1.1, -0.9, -1.2, -0.8]
    res = wilcoxon_signed_rank_test(diffs)
    assert res["n"] == 12
    assert res["w_plus"] == 0.0  # All negative differences
    assert res["w_minus"] > 0
    assert res["statistically_significant"] if "statistically_significant" in res else res["p_value"] < 0.05
    assert res["p_value"] < 0.05

def test_wilcoxon_signed_rank_test_not_significant():
    # Random differences around zero
    diffs = [0.5, -0.3, 0.2, -0.1, 0.4, -0.2, 0.1, -0.4]
    res = wilcoxon_signed_rank_test(diffs)
    assert res["n"] == 8
    assert res["w_plus"] > 0
    assert res["w_minus"] > 0
    # Not significant due to mixed signs
    assert res["p_value"] > 0.05

def test_wilcoxon_signed_rank_test_zero_differences():
    # All zeros should return p=1
    diffs = [0.0, 0.0, 0.0]
    res = wilcoxon_signed_rank_test(diffs)
    assert res["n"] == 0
    assert res["p_value"] == 1.0

def test_compare_model_runs_statistical_regression():
    y_true = ["10.0", "20.0", "30.0", "40.0"] * 10
    pred_a = ["10.1", "20.1", "30.1", "40.1"] * 10  # low error
    pred_b = ["12.0", "23.0", "34.0", "45.0"] * 10  # high error
    res = compare_model_runs_statistical(y_true, pred_a, pred_b, task_type="regression")
    assert res["winner"] == "model_a"
    assert res["statistically_significant"] is True
    assert "Wilcoxon" in res["test_type"]