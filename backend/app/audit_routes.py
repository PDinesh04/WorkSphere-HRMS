from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_roles
from app.audit_models import AuditLog

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


"""@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
    user=Depends(require_roles("ADMIN")),
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )"""

@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
    user=Depends(require_roles("ADMIN")),
):
    from app.audit_models import AuditLog

    logs = db.query(AuditLog).all()
    print("AUDIT LOG COUNT:", len(logs))
    return logs