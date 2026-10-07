import math
from typing import Any, Dict, List, Optional, Tuple

def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    probabilities: Optional[List[Optional[float]]] = None,
) -> Dict[str, float]:
    n = len(y_true)
    if n == 0:
        return {}

    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / n

    # Unique classes
    classes = sorted(list(set(y_true) | set(y_pred)))
    
    # Per-class precision, recall, f1
    precisions = []
    recalls = []
    f1s = []

    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    macro_precision = sum(precisions) / len(classes) if classes else 0.0
    macro_recall = sum(recalls) / len(classes) if classes else 0.0
    macro_f1 = sum(f1s) / len(classes) if classes else 0.0

    metrics: Dict[str, float] = {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
    }

    # Binary classification specific metrics if applicable
    if len(classes) == 2 and probabilities is not None:
        valid_pairs = [
            (yt, p) for yt, p in zip(y_true, probabilities) if p is not None
        ]
        if valid_pairs:
            pos_class = classes[1]  # alphabetically higher or '1'
            y_binary = [1 if yt == pos_class else 0 for yt, _ in valid_pairs]
            p_scores = [p for _, p in valid_pairs]

            # Brier Score
            brier = sum((p - y) ** 2 for y, p in zip(y_binary, p_scores)) / len(valid_pairs)
            metrics["brier_score"] = round(brier, 4)

            # Log Loss
            eps = 1e-15
            log_loss = -sum(
                y * math.log(max(p, eps)) + (1 - y) * math.log(max(1.0 - p, eps))
                for y, p in zip(y_binary, p_scores)
            ) / len(valid_pairs)
            metrics["log_loss"] = round(log_loss, 4)

            # ROC-AUC using Mann-Whitney U rank statistic
            pos_count = sum(y_binary)
            neg_count = len(y_binary) - pos_count
            if pos_count > 0 and neg_count > 0:
                indexed_scores = sorted(enumerate(p_scores), key=lambda x: x[1])
                ranks = [0.0] * len(indexed_scores)
                i = 0
                while i < len(indexed_scores):
                    j = i
                    while j < len(indexed_scores) and indexed_scores[j][1] == indexed_scores[i][1]:
                        j += 1
                    avg_rank = (i + 1 + j) / 2.0
                    for k in range(i, j):
                        ranks[indexed_scores[k][0]] = avg_rank
                    i = j
                rank_sum_pos = sum(ranks[idx] for idx, y in enumerate(y_binary) if y == 1)
                u_stat = rank_sum_pos - (pos_count * (pos_count + 1)) / 2.0
                roc_auc = u_stat / (pos_count * neg_count)
                metrics["roc_auc"] = round(roc_auc, 4)

            # ECE (Expected Calibration Error)
            ece, mce, _ = compute_calibration_curve(y_binary, p_scores, num_bins=10)
            metrics["expected_calibration_error"] = round(ece, 4)
            metrics["max_calibration_error"] = round(mce, 4)

    return metrics

def compute_calibration_curve(
    y_true_binary: List[int],
    probabilities: List[float],
    num_bins: int = 10,
) -> Tuple[float, float, List[Dict[str, Any]]]:
    n = len(y_true_binary)
    if n == 0:
        return 0.0, 0.0, []

    bins_data: List[Dict[str, Any]] = []
    bin_size = 1.0 / num_bins
    total_ece = 0.0
    max_ce = 0.0

    for b in range(num_bins):
        lower = b * bin_size
        upper = (b + 1) * bin_size
        in_bin = [
            (y, p)
            for y, p in zip(y_true_binary, probabilities)
            if (lower <= p < upper) or (b == num_bins - 1 and lower <= p <= upper)
        ]

        sample_count = len(in_bin)
        if sample_count > 0:
            mean_prob = sum(p for _, p in in_bin) / sample_count
            empirical_acc = sum(y for y, _ in in_bin) / sample_count
            gap = abs(empirical_acc - mean_prob)
            total_ece += (sample_count / n) * gap
            max_ce = max(max_ce, gap)
        else:
            mean_prob = (lower + upper) / 2.0
            empirical_acc = 0.0

        bins_data.append({
            "bin_index": b,
            "bin_center": round((lower + upper) / 2.0, 3),
            "sample_count": sample_count,
            "mean_predicted_prob": round(mean_prob, 4),
            "empirical_accuracy": round(empirical_acc, 4),
        })

    return total_ece, max_ce, bins_data

def compute_regression_metrics(
    y_true: List[float],
    y_pred: List[float],
) -> Dict[str, float]:
    n = len(y_true)
    if n == 0:
        return {}

    errors = [yp - yt for yt, yp in zip(y_true, y_pred)]
    abs_errors = [abs(e) for e in errors]
    sq_errors = [e ** 2 for e in errors]

    mse = sum(sq_errors) / n
    rmse = math.sqrt(mse)
    mae = sum(abs_errors) / n

    # MAPE
    non_zero_pairs = [(yt, yp) for yt, yp in zip(y_true, y_pred) if abs(yt) > 1e-9]
    mape = (
        sum(abs((yp - yt) / yt) for yt, yp in non_zero_pairs) / len(non_zero_pairs) * 100.0
        if non_zero_pairs else 0.0
    )

    # R-squared
    mean_true = sum(y_true) / n
    ss_tot = sum((yt - mean_true) ** 2 for yt in y_true)
    ss_res = sum(sq_errors)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    # Pearson correlation r
    mean_pred = sum(y_pred) / n
    cov = sum((yt - mean_true) * (yp - mean_pred) for yt, yp in zip(y_true, y_pred))
    var_true = sum((yt - mean_true) ** 2 for yt in y_true)
    var_pred = sum((yp - mean_pred) ** 2 for yp in y_pred)
    denom = math.sqrt(var_true * var_pred)
    pearson_r = cov / denom if denom > 1e-12 else 0.0

    return {
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 4),
        "r2": round(r2, 4),
        "pearson_r": round(pearson_r, 4),
    }
