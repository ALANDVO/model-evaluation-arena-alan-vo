import math
import random
from typing import Any, Callable, Dict, List, Optional, Tuple
from app.services.eval_metrics import compute_classification_metrics, compute_regression_metrics

def bootstrap_confidence_interval(
    values: List[float],
    confidence_level: float = 0.95,
) -> Tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    alpha = 1.0 - confidence_level
    lower_idx = int(math.floor((alpha / 2.0) * n))
    upper_idx = int(math.ceil((1.0 - alpha / 2.0) * n)) - 1
    lower_idx = max(0, min(n - 1, lower_idx))
    upper_idx = max(0, min(n - 1, upper_idx))

    mean_val = sum(sorted_vals) / n
    variance = sum((v - mean_val) ** 2 for v in sorted_vals) / (n - 1) if n > 1 else 0.0
    se = math.sqrt(variance)

    return sorted_vals[lower_idx], sorted_vals[upper_idx], se

def bootstrap_model_metrics(
    y_true: List[str],
    y_pred: List[str],
    task_type: str = "classification",
    probabilities: Optional[List[Optional[float]]] = None,
    resamples: int = 500,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    n = len(y_true)
    if n == 0:
        return {}, {}

    rng = random.Random(seed)

    # Point estimates on full dataset
    if task_type == "classification":
        point_metrics = compute_classification_metrics(y_true, y_pred, probabilities)
    else:
        y_true_float = [float(y) for y in y_true]
        y_pred_float = [float(y) for y in y_pred]
        point_metrics = compute_regression_metrics(y_true_float, y_pred_float)

    bootstrap_replicates: Dict[str, List[float]] = {m: [] for m in point_metrics.keys()}

    for _ in range(resamples):
        sample_indices = [rng.randint(0, n - 1) for _ in range(n)]
        sampled_true = [y_true[i] for i in sample_indices]
        sampled_pred = [y_pred[i] for i in sample_indices]

        if task_type == "classification":
            sampled_probs = [probabilities[i] for i in sample_indices] if probabilities else None
            m_res = compute_classification_metrics(sampled_true, sampled_pred, sampled_probs)
        else:
            sampled_true_f = [float(y) for y in sampled_true]
            sampled_pred_f = [float(y) for y in sampled_pred]
            m_res = compute_regression_metrics(sampled_true_f, sampled_pred_f)

        for metric_name, val in m_res.items():
            if metric_name in bootstrap_replicates:
                bootstrap_replicates[metric_name].append(val)

    ci_results: Dict[str, Dict[str, float]] = {}
    for metric_name, rep_vals in bootstrap_replicates.items():
        if rep_vals:
            lower, upper, se = bootstrap_confidence_interval(rep_vals, confidence_level)
            ci_results[metric_name] = {
                "point_estimate": point_metrics.get(metric_name, 0.0),
                "ci_lower": round(lower, 4),
                "ci_upper": round(upper, 4),
                "confidence_level": confidence_level,
                "standard_error": round(se, 4),
            }

    return point_metrics, ci_results

def paired_bootstrap_comparison(
    y_true: List[str],
    pred_a: List[str],
    pred_b: List[str],
    task_type: str = "classification",
    metric_name: str = "accuracy",
    resamples: int = 500,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Dict[str, Any]:
    n = len(y_true)
    if n == 0:
        return {
            "difference": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "p_value": 1.0,
            "statistically_significant": False,
        }

    rng = random.Random(seed)

    def calc_metric(y_t: List[str], y_p: List[str]) -> float:
        if task_type == "classification":
            m = compute_classification_metrics(y_t, y_p)
        else:
            m = compute_regression_metrics([float(y) for y in y_t], [float(y) for y in y_p])
        return m.get(metric_name, 0.0)

    obs_metric_a = calc_metric(y_true, pred_a)
    obs_metric_b = calc_metric(y_true, pred_b)
    obs_diff = obs_metric_a - obs_metric_b

    diffs: List[float] = []
    for _ in range(resamples):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        s_true = [y_true[i] for i in indices]
        s_a = [pred_a[i] for i in indices]
        s_b = [pred_b[i] for i in indices]

        diff_b = calc_metric(s_true, s_a) - calc_metric(s_true, s_b)
        diffs.append(diff_b)

    ci_low, ci_high, se = bootstrap_confidence_interval(diffs, confidence_level)

    # Two-sided empirical p-value
    count_le_zero = sum(1 for d in diffs if d <= 0)
    count_ge_zero = sum(1 for d in diffs if d >= 0)
    p_val = 2.0 * min(count_le_zero, count_ge_zero) / len(diffs)
    p_val = min(1.0, max(0.001, p_val))

    sig = (ci_low > 0 or ci_high < 0) or (p_val < (1.0 - confidence_level))

    return {
        "difference": round(obs_diff, 4),
        "ci_lower": round(ci_low, 4),
        "ci_upper": round(ci_high, 4),
        "p_value": round(p_val, 4),
        "statistically_significant": sig,
        "standard_error": round(se, 4),
    }
