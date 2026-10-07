import pytest
from app.services.slice_analysis import analyze_cohort_slices

def test_analyze_cohort_slices():
    cohorts = [
        {"region": "US", "tier": "premium"},
        {"region": "US", "tier": "free"},
        {"region": "EU", "tier": "premium"},
        {"region": "EU", "tier": "free"},
    ]
    y_true = ["1", "1", "1", "1"]
    preds_by_model = {
        "1": ["1", "1", "1", "0"],  # misses EU free
        "2": ["1", "1", "1", "1"],  # perfect
    }
    slices = analyze_cohort_slices(cohorts, y_true, preds_by_model, task_type="classification")
    assert len(slices) >= 4  # 2 regions + 2 tiers
    # Check that at least one slice is flagged as worst slice
    worst = [s for s in slices if s["is_worst_slice"]]
    assert len(worst) == 1
    assert any(s["cohort_name"] == "region" for s in slices)
    assert any(s["cohort_name"] == "tier" for s in slices)
