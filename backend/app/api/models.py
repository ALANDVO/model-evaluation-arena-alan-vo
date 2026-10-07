import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, verify_csrf
from app.models.entities import Dataset, DatasetItem, ModelRun, Prediction
from app.models.schemas import ModelRunCreate, ModelRunResponse, PredictionBatchUpload
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("", response_model=List[ModelRunResponse])
def list_models(dataset_id: Optional[int] = None, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(ModelRun)
    if dataset_id is not None: q = q.filter(ModelRun.dataset_id == dataset_id)
    runs = q.order_by(ModelRun.id.desc()).offset(skip).limit(limit).all()
    res = []
    for r in runs:
        cnt = db.query(Prediction).filter(Prediction.model_run_id == r.id).count()
        res.append(ModelRunResponse(id=r.id, dataset_id=r.dataset_id, name=r.name, version=r.version, architecture=r.architecture, description=r.description, prediction_count=cnt, created_by=r.created_by, created_at=r.created_at))
    return res

@router.get("/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    r = db.query(ModelRun).filter(ModelRun.id == model_id).first()
    if not r: raise HTTPException(404, "Model run not found")
    cnt = db.query(Prediction).filter(Prediction.model_run_id == r.id).count()
    preds = db.query(Prediction).filter(Prediction.model_run_id == r.id).limit(50).all()
    return {"id": r.id, "dataset_id": r.dataset_id, "name": r.name, "version": r.version, "architecture": r.architecture, "description": r.description, "prediction_count": cnt, "sample_predictions": [{"id": p.id, "item_key": p.item_key, "predicted_label": p.predicted_label, "probability": p.probability} for p in preds], "created_by": r.created_by, "created_at": r.created_at}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_model_run(body: ModelRunCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_role(["analyst", "admin"])), _csrf: None = Depends(verify_csrf)):
    if not db.query(Dataset).filter(Dataset.id == body.dataset_id).first():
        raise HTTPException(404, "Dataset not found")
    run = ModelRun(dataset_id=body.dataset_id, name=body.name, version=body.version, architecture=body.architecture, description=body.description, created_by=current_user.get("username", "analyst"))
    db.add(run); db.commit(); db.refresh(run)
    log_audit_event(db, current_user.get("username", "user"), "create_model_run", "model_run", str(run.id), {"name": run.name})
    return {"id": run.id, "dataset_id": run.dataset_id, "name": run.name, "version": run.version, "architecture": run.architecture, "description": run.description, "prediction_count": 0, "created_by": run.created_by, "created_at": run.created_at}

@router.post("/{model_id}/predictions")
def upload_predictions(model_id: int, body: PredictionBatchUpload, db: Session = Depends(get_db), current_user: dict = Depends(require_role(["analyst", "admin"])), _csrf: None = Depends(verify_csrf)):
    run = db.query(ModelRun).filter(ModelRun.id == model_id).first()
    if not run: raise HTTPException(404, "Model run not found")
    valid_keys = {row[0] for row in db.query(DatasetItem.item_key).filter(DatasetItem.dataset_id == run.dataset_id).all()}
    if not valid_keys: raise HTTPException(400, "Dataset has no items registered")
    matched = 0
    for p in body.predictions:
        if p.item_key not in valid_keys: continue
        db.add(Prediction(model_run_id=run.id, item_key=p.item_key, predicted_label=str(p.predicted_label), probability=p.probability, probabilities_json=json.dumps(p.probabilities) if p.probabilities else None))
        matched += 1
    db.commit()
    log_audit_event(db, current_user.get("username", "user"), "upload_predictions", "model_run", str(run.id), {"count": matched})
    return {"model_id": run.id, "submitted": len(body.predictions), "matched_and_saved": matched, "total_predictions": db.query(Prediction).filter(Prediction.model_run_id == run.id).count()}

@router.delete("/{model_id}")
def delete_model_run(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role(["admin"])), _csrf: None = Depends(verify_csrf)):
    run = db.query(ModelRun).filter(ModelRun.id == model_id).first()
    if not run: raise HTTPException(404, "Model run not found")
    db.delete(run); db.commit()
    log_audit_event(db, current_user.get("username", "user"), "delete_model_run", "model_run", str(model_id), {"name": run.name})
    return {"status": "deleted", "model_id": model_id}
