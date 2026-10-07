import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, verify_csrf
from app.models.entities import Dataset, DatasetItem
from app.models.schemas import DatasetCreate, DatasetItemCreate, DatasetResponse
from app.services.audit import log_audit_event

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.get("", response_model=List[DatasetResponse])
def list_datasets(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), task_type: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = db.query(Dataset)
    if task_type: q = q.filter(Dataset.task_type == task_type)
    datasets = q.order_by(Dataset.id.desc()).offset(skip).limit(limit).all()
    res = []
    for d in datasets:
        cnt = db.query(DatasetItem).filter(DatasetItem.dataset_id == d.id).count()
        res.append(DatasetResponse(id=d.id, name=d.name, description=d.description, task_type=d.task_type, target_column=d.target_column, cohort_columns=json.loads(d.cohort_columns or "[]"), item_count=cnt, created_by=d.created_by, created_at=d.created_at, updated_at=d.updated_at))
    return res

@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    d = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not d: raise HTTPException(404, "Dataset not found")
    items = db.query(DatasetItem).filter(DatasetItem.dataset_id == d.id).limit(100).all()
    cnt = db.query(DatasetItem).filter(DatasetItem.dataset_id == d.id).count()
    samples = [{"id": it.id, "item_key": it.item_key, "ground_truth": it.ground_truth, "cohorts": json.loads(it.cohorts_json), "metadata": json.loads(it.metadata_json)} for it in items]
    return {"id": d.id, "name": d.name, "description": d.description, "task_type": d.task_type, "target_column": d.target_column, "cohort_columns": json.loads(d.cohort_columns or "[]"), "item_count": cnt, "sample_items": samples, "created_by": d.created_by, "created_at": d.created_at, "updated_at": d.updated_at}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_dataset(body: DatasetCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_role(["analyst", "admin"])), _csrf: None = Depends(verify_csrf)):
    if db.query(Dataset).filter(Dataset.name == body.name).first():
        raise HTTPException(400, "Dataset name already exists")
    ds = Dataset(name=body.name, description=body.description, task_type=body.task_type, target_column=body.target_column, cohort_columns=json.dumps(body.cohort_columns), created_by=current_user.get("username", "analyst"))
    db.add(ds); db.commit(); db.refresh(ds)
    log_audit_event(db, current_user.get("username", "user"), "create_dataset", "dataset", str(ds.id), {"name": ds.name})
    return {"id": ds.id, "name": ds.name, "description": ds.description, "task_type": ds.task_type, "target_column": ds.target_column, "cohort_columns": body.cohort_columns, "item_count": 0, "created_by": ds.created_by, "created_at": ds.created_at, "updated_at": ds.updated_at}

@router.post("/{dataset_id}/items")
def upload_dataset_items(dataset_id: int, items: List[DatasetItemCreate], db: Session = Depends(get_db), current_user: dict = Depends(require_role(["analyst", "admin"])), _csrf: None = Depends(verify_csrf)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    for it in items:
        db.add(DatasetItem(dataset_id=ds.id, item_key=it.item_key, ground_truth=it.ground_truth, cohorts_json=json.dumps(it.cohorts), metadata_json=json.dumps(it.metadata)))
    db.commit()
    log_audit_event(db, current_user.get("username", "user"), "upload_dataset_items", "dataset", str(ds.id), {"count": len(items)})
    return {"dataset_id": ds.id, "uploaded_count": len(items), "total_items": db.query(DatasetItem).filter(DatasetItem.dataset_id == ds.id).count()}

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role(["admin"])), _csrf: None = Depends(verify_csrf)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    db.delete(ds); db.commit()
    log_audit_event(db, current_user.get("username", "user"), "delete_dataset", "dataset", str(dataset_id), {"name": ds.name})
    return {"status": "deleted", "dataset_id": dataset_id}
