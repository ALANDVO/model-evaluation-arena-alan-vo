import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, require_role, verify_csrf
from app.models.entities import Dataset, DatasetItem, ModelRun, Prediction
from app.models.schemas import AdvisoryAuditRequest, AdvisoryAuditResponse
from app.services.audit import log_audit_event
from app.services.bootstrap import bootstrap_model_metrics, paired_bootstrap_comparison
from app.services.llm_advisor import call_llm_advisor
from app.services.slice_analysis import analyze_cohort_slices

router = APIRouter(prefix="/api/llm", tags=["llm"])

@router.get("/config")
def get_llm_config(current_user: dict = Depends(get_current_user)):
    return {
        "provider": settings.llm_provider,
        "base_url": settings.llm_base_url,
        "model": settings.llm_model,
        "is_configured": bool(settings.llm_api_key and settings.llm_api_key.strip()),
        "timeout_seconds": settings.llm_timeout_seconds,
    }

@router.post("/audit", response_model=AdvisoryAuditResponse)
async def generate_advisory_audit(
    body: AdvisoryAuditRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    _csrf: None = Depends(verify_csrf),
):
    ds = db.query(Dataset).filter(Dataset.id == body.dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    items = db.query(DatasetItem).filter(DatasetItem.dataset_id == ds.id).all()
    if not items:
        raise HTTPException(status_code=400, detail="Dataset has no items")

    runs = (
        db.query(ModelRun)
        .filter(ModelRun.id.in_(body.model_run_ids), ModelRun.dataset_id == ds.id)
        .all()
    )
    if not runs:
        raise HTTPException(status_code=400, detail="No matching model runs found")

    item_keys = [it.item_key for it in items]
    y_true = [it.ground_truth for it in items]
    cohorts_list = [json.loads(it.cohorts_json) for it in items]

    models_summary = {}
    preds_by_model = {}

    for r in runs:
        preds = db.query(Prediction).filter(Prediction.model_run_id == r.id).all()
        pred_map = {p.item_key: (p.predicted_label, p.probability) for p in preds}

        aligned_labels = [
            pred_map.get(k, ("0" if ds.task_type == "classification" else "0.0", 0.5))[0]
            for k in item_keys
        ]
        aligned_probs = [
            pred_map.get(k, ("0", 0.5))[1] for k in item_keys
        ]
        preds_by_model[str(r.id)] = aligned_labels

        point_m, ci_m = bootstrap_model_metrics(
            y_true=y_true,
            y_pred=aligned_labels,
            task_type=ds.task_type,
            probabilities=aligned_probs if ds.task_type == "classification" else None,
            resamples=200,
        )
        models_summary[r.name] = {
            "metrics": point_m,
            "bootstrap_95_ci": ci_m,
        }

    # Run paired comparisons
    paired_list = []
    run_list = list(runs)
    metric_focus = body.focus_metric or ("accuracy" if ds.task_type == "classification" else "rmse")
    for i in range(len(run_list)):
        for j in range(i + 1, len(run_list)):
            r_a = run_list[i]
            r_b = run_list[j]
            comp = paired_bootstrap_comparison(
                y_true=y_true,
                pred_a=preds_by_model[str(r_a.id)],
                pred_b=preds_by_model[str(r_b.id)],
                task_type=ds.task_type,
                metric_name=metric_focus,
                resamples=200,
            )
            paired_list.append({
                "model_a_name": r_a.name,
                "model_b_name": r_b.name,
                "difference": comp["difference"],
                "p_value": comp["p_value"],
                "statistically_significant": comp["statistically_significant"],
                "winner": r_a.name if comp["difference"] > 0 else r_b.name,
            })

    # Find worst slice
    slices = analyze_cohort_slices(
        items_cohorts=cohorts_list,
        y_true=y_true,
        predictions_by_model=preds_by_model,
        task_type=ds.task_type,
    )
    worst_slice = next((s for s in slices if s.get("is_worst_slice")), None)

    # Call LLM advisor
    result = await call_llm_advisor(
        dataset_name=ds.name,
        task_type=ds.task_type,
        models_summary=models_summary,
        paired_tests=paired_list,
        worst_slice=worst_slice,
        user_context=body.user_context,
    )

    log_audit_event(
        db,
        user_id=current_user.get("username", "user"),
        action="generate_advisory_audit",
        resource_type="llm_advisory",
        resource_id=str(ds.id),
        details={"status": result["status"], "provider": result["provider"]},
    )

    return AdvisoryAuditResponse(
        status=result["status"],
        provider=result["provider"],
        model=result["model"],
        analysis=result["analysis"],
        advisory_disclaimer=result["advisory_disclaimer"],
        grounded_evidence=result["grounded_evidence"],
    )
