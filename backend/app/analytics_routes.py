
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_roles
from app import models
from app.resignation_models import Resignation
from app.settlement_models import FinalSettlement

router = APIRouter(
    prefix="/analytics",
    tags=["HR Analytics"],
)


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    total_employees = db.query(models.Employee).count()

    active_employees = db.query(models.Employee).filter(
        models.Employee.status == "ACTIVE"
    ).count()

    total_resignations = db.query(Resignation).count()

    pending_resignations = db.query(Resignation).filter(
        Resignation.status == "PENDING"
    ).count()

    total_settlements = db.query(FinalSettlement).count()

    pending_settlements = db.query(FinalSettlement).filter(
        FinalSettlement.status == "PENDING"
    ).count()

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_resignations": total_resignations,
        "pending_resignations": pending_resignations,
        "total_settlements": total_settlements,
        "pending_settlements": pending_settlements,
    }
