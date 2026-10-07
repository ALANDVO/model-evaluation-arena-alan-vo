import datetime, io, json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, verify_csrf
from app.models.entities import Dataset, DatasetItem, EvaluationReport, ModelRun, Prediction
from app.models.schemas import (
    ArenaEvaluationRequest, ArenaEvaluationResponse, ConfidenceInterval,
    ModelMetrics, PairedHypothesisResult, ReliabilityDiagram, SliceDisparityResult,
)
from app.services.audit import log_audit_event
from app.services.bootstrap import bootstrap_model_metrics, paired_bootstrap_comparison
from app.services.eval_metrics import compute_calibration_curve
from app.services.slice_analysis import analyze_cohort_slices
from app.services.statistical_tests import compare_model_runs_statistical

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

@router.post("/run", response_model=ArenaEvaluationResponse)
def run_evaluation(
    body: ArenaEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    _csrf: None = Depends(verify_csrf),
):
    ds = db.query(Dataset).filter(Dataset.id == body.dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")

    items = db.query(DatasetItem).filter(DatasetItem.dataset_id == ds.id).order_by(DatasetItem.id.asc()).all()
    if not items: raise HTTPException(400, "Dataset has no items to evaluate")

    item_keys = [it.item_key for it in items]
    y_true = [it.ground_truth for it in items]
    cohorts_list = [json.loads(it.cohorts_json) for it in items]

    runs = db.query(ModelRun).filter(ModelRun.id.in_(body.model_run_ids), ModelRun.dataset_id == ds.id).all()
    if not runs: raise HTTPException(400, "No matching model runs found")

    model_preds: Dict[int, List[str]] = {}
    model_probs: Dict[int, List[Optional[float]]] = {}

    for r in runs:
        preds = db.query(Prediction).filter(Prediction.model_run_id == r.id).all()
        pmap = {p.item_key: (p.predicted_label, p.probability) for p in preds}
        model_preds[r.id] = [pmap.get(k, ("0" if ds.task_type == "classification" else "0.0", 0.5))[0] for k in item_keys]
        model_probs[r.id] = [pmap.get(k, ("0", 0.5))[1] for k in item_keys]

    models_metrics_list: List[ModelMetrics] = []
    reliability_diagrams: List[ReliabilityDiagram] = []

    for r in runs:
        preds, probs = model_preds[r.id], model_probs[r.id]
        point_m, ci_m = bootstrap_model_metrics(
            y_true=y_true, y_pred=preds, task_type=ds.task_type,
            probabilities=probs if ds.task_type == "classification" else None,
            resamples=body.resamples, confidence_level=body.confidence_level,
        )
        models_metrics_list.append(ModelMetrics(
            model_run_id=r.id, model_name=r.name, sample_size=len(items), metrics=point_m,
            bootstrap_cis={k: ConfidenceInterval(**v) for k, v in ci_m.items()},
        ))

        if ds.task_type == "classification" and probs and any(p is not None for p in probs):
            classes = sorted(list(set(y_true)))
            if len(classes) == 2:
                y_bin = [1 if yt == classes[1] else 0 for yt in y_true]
                clean_probs = [p if p is not None else 0.5 for p in probs]
                ece, mce, bins = compute_calibration_curve(y_bin, clean_probs, num_bins=10)
                reliability_diagrams.append(ReliabilityDiagram(
                    model_run_id=r.id, model_name=r.name, expected_calibration_error=round(ece, 4),
                    max_calibration_error=round(mce, 4), brier_score=round(point_m.get("brier_score", 0.0), 4), bins=bins,
                ))

    paired_results: List[PairedHypothesisResult] = []
    metric_focus = "accuracy" if ds.task_type == "classification" else "rmse"
    run_list = list(runs)
    for i in range(len(run_list)):
        for j in range(i + 1, len(run_list)):
            ra, rb = run_list[i], run_list[j]
            bd = paired_bootstrap_comparison(y_true, model_preds[ra.id], model_preds[rb.id], ds.task_type, metric_focus, body.resamples, body.confidence_level)
            st = compare_model_runs_statistical(y_true, model_preds[ra.id], model_preds[rb.id], ds.task_type)
            winner = ra.id if st.get("winner") == "model_a" else (rb.id if st.get("winner") == "model_b" else None)
            paired_results.append(PairedHypothesisResult(
                model_a_id=ra.id, model_a_name=ra.name, model_b_id=rb.id, model_b_name=rb.name,
                metric_name=metric_focus, difference=bd["difference"], ci_lower=bd["ci_lower"], ci_upper=bd["ci_upper"],
                p_value=st.get("p_value", bd["p_value"]), statistically_significant=st.get("statistically_significant", False),
                test_type=st.get("test_type", "Paired Bootstrap"), winner_id=winner,
            ))

    slices_raw = analyze_cohort_slices(cohorts_list, y_true, {str(r.id): model_preds[r.id] for r in runs}, ds.task_type)
    slice_breakdowns = [SliceDisparityResult(**s) for s in slices_raw]

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    report_record = EvaluationReport(
        dataset_id=ds.id, title=f"{ds.name} Arena Benchmark ({len(runs)} models)",
        model_run_ids=json.dumps([r.id for r in runs]),
        metrics_summary=json.dumps([m.model_dump() for m in models_metrics_list]),
        bootstrap_results=json.dumps({str(m.model_run_id): {k: v.model_dump() for k, v in m.bootstrap_cis.items()} for m in models_metrics_list}),
        slice_disparities=json.dumps([s.model_dump() for s in slice_breakdowns]),
        paired_comparisons=json.dumps([p.model_dump() for p in paired_results]),
        created_by=current_user.get("username", "analyst"), created_at=now_utc,
    )
    db.add(report_record); db.commit(); db.refresh(report_record)

    log_audit_event(db, current_user.get("username", "user"), "run_evaluation", "evaluation_report", str(report_record.id), {"dataset_id": ds.id})
    return ArenaEvaluationResponse(
        report_id=report_record.id, dataset_id=ds.id, dataset_name=ds.name, task_type=ds.task_type,
        models=models_metrics_list, paired_tests=paired_results, slice_breakdowns=slice_breakdowns,
        calibration_diagrams=reliability_diagrams or None, generated_at=now_utc,
    )

@router.get("/reports")
def list_reports(dataset_id: Optional[int] = None, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(EvaluationReport)
    if dataset_id: q = q.filter(EvaluationReport.dataset_id == dataset_id)
    return [{"id": r.id, "dataset_id": r.dataset_id, "title": r.title, "model_run_ids": json.loads(r.model_run_ids), "created_by": r.created_by, "created_at": r.created_at} for r in q.order_by(EvaluationReport.id.desc()).offset(skip).limit(limit).all()]

@router.get("/export/{report_id}")
def export_report(report_id: int, format: str = Query("json", pattern="^(json|csv)$"), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    r = db.query(EvaluationReport).filter(EvaluationReport.id == report_id).first()
    if not r: raise HTTPException(404, "Evaluation report not found")
    metrics_list = json.loads(r.metrics_summary)
    if format == "json":
        data = {"report_id": r.id, "title": r.title, "dataset_id": r.dataset_id, "models_summary": metrics_list, "paired_comparisons": json.loads(r.paired_comparisons), "slice_disparities": json.loads(r.slice_disparities), "created_at": r.created_at.isoformat()}
        return Response(content=json.dumps(data, indent=2), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=arena_report_{report_id}.json"})
    out = io.StringIO()
    out.write("model_run_id,model_name,sample_size,metric_name,point_estimate,ci_lower,ci_upper,standard_error\n")
    for m in metrics_list:
        m_id, m_name, sz = m.get("model_run_id"), m.get("model_name"), m.get("sample_size")
        for k, v in m.get("bootstrap_cis", {}).items():
            out.write(f"{m_id},{m_name},{sz},{k},{v.get('point_estimate')},{v.get('ci_lower')},{v.get('ci_upper')},{v.get('standard_error')}\n")
    return Response(content=out.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=arena_report_{report_id}.csv"})
