import json
from typing import Any, Dict, List, Optional
from app.services.eval_metrics import compute_classification_metrics, compute_regression_metrics

def analyze_cohort_slices(
    items_cohorts: List[Dict[str, str]],
    y_true: List[str],
    predictions_by_model: Dict[str, List[str]],  # model_id -> list of predictions
    task_type: str = "classification",
    target_metric: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not items_cohorts or not y_true:
        return []

    if target_metric is None:
        target_metric = "accuracy" if task_type == "classification" else "rmse"

    # Identify all cohort keys
    cohort_keys = set()
    for c_map in items_cohorts:
        cohort_keys.update(c_map.keys())

    total_samples = len(y_true)
    results: List[Dict[str, Any]] = []

    for key in sorted(list(cohort_keys)):
        # Group indices by cohort value
        groups: Dict[str, List[int]] = {}
        for idx, c_map in enumerate(items_cohorts):
            val = c_map.get(key, "unspecified")
            groups.setdefault(val, []).append(idx)

        # Compute metric for each cohort value across models
        slice_scores_for_key: Dict[str, Dict[str, float]] = {}

        for val, idx_list in groups.items():
            slice_true = [y_true[i] for i in idx_list]
            model_metrics_map: Dict[str, Dict[str, float]] = {}

            for model_id, preds in predictions_by_model.items():
                slice_pred = [preds[i] for i in idx_list]
                if task_type == "classification":
                    m = compute_classification_metrics(slice_true, slice_pred)
                else:
                    true_f = [float(y) for y in slice_true]
                    pred_f = [float(y) for y in slice_pred]
                    m = compute_regression_metrics(true_f, pred_f)
                model_metrics_map[str(model_id)] = m

            slice_scores_for_key[val] = {
                model_id: mm.get(target_metric, 0.0)
                for model_id, mm in model_metrics_map.items()
            }

            sample_sz = len(idx_list)
            pct = round((sample_sz / total_samples) * 100.0, 2)

            results.append({
                "cohort_name": key,
                "cohort_value": val,
                "sample_size": sample_sz,
                "percentage_of_total": pct,
                "metrics_by_model": model_metrics_map,
                "target_metric": target_metric,
                "is_worst_slice": False,
                "disparity_ratio": None,
            })

        # Calculate disparity ratio for this cohort dimension
        for model_id in predictions_by_model.keys():
            scores = [
                slice_scores_for_key[v].get(str(model_id), 0.0)
                for v in groups.keys()
            ]
            if scores and min(scores) > 0 and max(scores) > 0:
                disp_ratio = round(min(scores) / max(scores), 4)
            else:
                disp_ratio = 1.0

            # Attach disparity to matching entries
            for entry in results:
                if entry["cohort_name"] == key:
                    entry["disparity_ratio"] = disp_ratio

    # Mark worst slice across cohorts based on average target metric
    if results:
        if task_type == "classification":
            # Lowest score is worst
            worst_entry = min(
                results,
                key=lambda x: sum(
                    mm.get(target_metric, 0.0) for mm in x["metrics_by_model"].values()
                ) / max(len(x["metrics_by_model"]), 1),
            )
        else:
            # Highest error is worst
            worst_entry = max(
                results,
                key=lambda x: sum(
                    mm.get(target_metric, 0.0) for mm in x["metrics_by_model"].values()
                ) / max(len(x["metrics_by_model"]), 1),
            )
        worst_entry["is_worst_slice"] = True

    return results
