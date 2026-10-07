import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.entities import AuditLog
from app.models.schemas import AuditLogEntry, PaginatedAuditLogs

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("", response_model=PaginatedAuditLogs)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["analyst", "admin"])),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    records = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()

    items = [
        AuditLogEntry(
            id=r.id,
            user_id=r.user_id,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            details=json.loads(r.details) if r.details else {},
            created_at=r.created_at,
        )
        for r in records
    ]
    return PaginatedAuditLogs(total=total, items=items)
