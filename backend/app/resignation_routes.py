
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app import models
from app.resignation_models import Resignation
from app.resignation_schemas import (
    ResignationCreate,
    ResignationStatusUpdate,
    ResignationResponse,
)

router = APIRouter(prefix="/resignations", tags=["Resignations"])


@router.post("/", response_model=ResignationResponse, status_code=201)
def submit_resignation(
    payload: ResignationCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    employee = (
        db.query(models.Employee)
        .filter_by(user_id=user.id)
        .first()
    )
    if not employee:
        raise HTTPException(404, "Employee profile not found")

    existing = db.query(Resignation).filter(
        Resignation.employee_id == employee.id,
        Resignation.status == "PENDING",
    ).first()
    if existing:
        raise HTTPException(409, "You already have a pending resignation")

    row = Resignation(
        employee_id=employee.id,
        reason=payload.reason.strip(),
        notice_period=payload.notice_period,
        status="PENDING",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=list[ResignationResponse])
def list_resignations(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(Resignation)

    if user.role not in ("HR", "ADMIN"):
        employee = (
            db.query(models.Employee)
            .filter_by(user_id=user.id)
            .first()
        )
        if not employee:
            raise HTTPException(404, "Employee profile not found")
        query = query.filter(Resignation.employee_id == employee.id)

    return query.order_by(Resignation.created_at.desc()).all()


@router.patch("/{resignation_id}/decision", response_model=ResignationResponse)
def decide_resignation(
    resignation_id: int,
    payload: ResignationStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    row = db.get(Resignation, resignation_id)
    if not row:
        raise HTTPException(404, "Resignation not found")
    if row.status != "PENDING":
        raise HTTPException(409, "Resignation has already been processed")

    row.status = payload.status
    db.commit()
    db.refresh(row)
    return row
