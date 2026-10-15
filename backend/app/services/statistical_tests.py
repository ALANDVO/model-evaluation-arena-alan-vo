import math
from typing import Dict, List, Tuple

def erf_approx(x: float) -> float:
    # High-precision approximation of Gauss error function
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return sign * y

def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf_approx(x / math.sqrt(2.0)))

def chi2_survival_1df(chi2: float) -> float:
    # P(X >= chi2) for df=1 is 2 * (1 - normal_cdf(sqrt(chi2)))
    if chi2 <= 0:
        return 1.0
    z = math.sqrt(chi2)
    return max(0.0001, min(1.0, 2.0 * (1.0 - normal_cdf(z))))

def wilcoxon_signed_rank_test(
    diffs: List[float],
) -> Dict[str, float]:
    """Wilcoxon signed-rank test for paired samples.

    Non-parametric alternative to paired t-test. Tests whether the median
    of the differences is zero (i.e., no systematic difference between pairs).
    """
    # Remove zero differences
    non_zero_diffs = [d for d in diffs if d != 0.0]
    n = len(non_zero_diffs)
    if n == 0:
        return {"statistic": 0.0, "p_value": 1.0, "n": 0, "w_plus": 0.0, "w_minus": 0.0}

    # Rank absolute differences (average ranks for ties)
    abs_diffs_with_idx = [(abs(d), i, d > 0) for i, d in enumerate(non_zero_diffs)]
    abs_diffs_with_idx.sort(key=lambda x: x[0])

    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        # Find all tied values
        while j < n and abs_diffs_with_idx[j][0] == abs_diffs_with_idx[i][0]:
            j += 1
        # Average rank for ties
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[abs_diffs_with_idx[k][1]] = avg_rank
        i = j

    # Sum ranks for positive and negative differences
    w_plus = sum(ranks[i] for i, (_, _, is_pos) in enumerate(abs_diffs_with_idx) if is_pos)
    w_minus = sum(ranks[i] for i, (_, _, is_pos) in enumerate(abs_diffs_with_idx) if not is_pos)

    # Test statistic is min(W+, W-)
    w_stat = min(w_plus, w_minus)

    # Normal approximation for n >= 10 (with continuity correction)
    if n >= 10:
        # Expected value and variance under null hypothesis
        expected_w = n * (n + 1) / 4.0
        # Variance with tie correction
        tie_groups: Dict[float, int] = {}
        for abs_val, _, _ in abs_diffs_with_idx:
            tie_groups[abs_val] = tie_groups.get(abs_val, 0) + 1
        tie_correction = sum(t * (t * t - 1) for t in tie_groups.values()) / 48.0
        variance = n * (n + 1) * (2 * n + 1) / 24.0 - tie_correction

        if variance <= 0:
            z = 0.0
        else:
            # Continuity correction: 0.5 in direction of alternative
            z = (w_stat - expected_w + 0.5) / math.sqrt(variance)
        p_val = 2.0 * normal_cdf(-abs(z))
    else:
        # Exact p-value for small n (simplified: use normal approx anyway for consistency)
        # For exact test, would need precomputed tables; using normal approx as fallback
        expected_w = n * (n + 1) / 4.0
        variance = n * (n + 1) * (2 * n + 1) / 24.0
        if variance <= 0:
            z = 0.0
        else:
            z = (w_stat - expected_w + 0.5) / math.sqrt(variance)
        p_val = 2.0 * normal_cdf(-abs(z))

    return {
        "statistic": round(w_stat, 4),
        "p_value": max(0.0001, min(1.0, round(p_val, 4))),
        "n": n,
        "w_plus": w_plus,
        "w_minus": w_minus,
    }

def mcnemar_test(
    y_true: List[str],
    pred_a: List[str],
    pred_b: List[str],
) -> Dict[str, float]:
    n = len(y_true)
    if n == 0:
        return {"statistic": 0.0, "p_value": 1.0, "b": 0, "c": 0}

    # b: A correct, B incorrect
    # c: A incorrect, B correct
    b = sum(1 for yt, pa, pb in zip(y_true, pred_a, pred_b) if pa == yt and pb != yt)
    c = sum(1 for yt, pa, pb in zip(y_true, pred_a, pred_b) if pa != yt and pb == yt)

    discordant = b + c
    if discordant == 0:
        return {"statistic": 0.0, "p_value": 1.0, "b": b, "c": c}

    # Edwards continuity correction
    stat = (abs(b - c) - 1.0) ** 2 / discordant if abs(b - c) >= 1 else 0.0
    p_val = chi2_survival_1df(stat)

    return {
        "statistic": round(stat, 4),
        "p_value": round(p_val, 4),
        "b": b,
        "c": c,
    }

def paired_t_test(
    diffs: List[float],
) -> Dict[str, float]:
    n = len(diffs)
    if n < 2:
        return {"statistic": 0.0, "p_value": 1.0}

    mean_d = sum(diffs) / n
    variance = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    if variance < 1e-12:
        return {"statistic": 0.0, "p_value": 1.0}

    se = math.sqrt(variance / n)
    t_stat = mean_d / se

    # Normal approximation for p-value with degrees of freedom >= 20
    p_val = 2.0 * (1.0 - normal_cdf(abs(t_stat)))
    p_val = max(0.0001, min(1.0, p_val))

    return {
        "statistic": round(t_stat, 4),
        "p_value": round(p_val, 4),
    }

def compare_model_runs_statistical(
    y_true: List[str],
    pred_a: List[str],
    pred_b: List[str],
    task_type: str = "classification",
) -> Dict[str, any]:
    if task_type == "classification":
        mcnemar = mcnemar_test(y_true, pred_a, pred_b)
        is_sig = mcnemar["p_value"] < 0.05
        winner = None
        if is_sig:
            if mcnemar["b"] > mcnemar["c"]:
                winner = "model_a"
            elif mcnemar["c"] > mcnemar["b"]:
                winner = "model_b"

        return {
            "test_type": "McNemar test with Edwards continuity correction",
            "statistic": mcnemar["statistic"],
            "p_value": mcnemar["p_value"],
            "statistically_significant": is_sig,
            "winner": winner,
            "details": f"Model A uniquely correct in {mcnemar['b']} instances; Model B uniquely correct in {mcnemar['c']} instances.",
        }
    else:
        # For regression, use Wilcoxon signed-rank test on absolute error residuals
        # (non-parametric alternative to paired t-test)
        true_f = [float(y) for y in y_true]
        pred_a_f = [float(y) for y in pred_a]
        pred_b_f = [float(y) for y in pred_b]

        err_a = [abs(yt - pa) for yt, pa in zip(true_f, pred_a_f)]
        err_b = [abs(yt - pb) for yt, pb in zip(true_f, pred_b_f)]
        diffs = [ea - eb for ea, eb in zip(err_a, err_b)]  # diff < 0 means A has lower error than B

        wilcoxon = wilcoxon_signed_rank_test(diffs)
        is_sig = wilcoxon["p_value"] < 0.05
        mean_diff = sum(diffs) / len(diffs) if diffs else 0.0
        winner = None
        if is_sig:
            if mean_diff < 0:
                winner = "model_a"
            elif mean_diff > 0:
                winner = "model_b"

        return {
            "test_type": "Wilcoxon signed-rank test on absolute residual errors",
            "statistic": wilcoxon["statistic"],
            "p_value": wilcoxon["p_value"],
            "statistically_significant": is_sig,
            "winner": winner,
            "details": f"Mean difference in absolute error: {round(mean_diff, 4)}. W+={wilcoxon['w_plus']}, W-={wilcoxon['w_minus']}.",
        }