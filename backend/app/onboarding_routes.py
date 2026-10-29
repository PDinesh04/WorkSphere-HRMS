
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app import models
from app.onboarding_models import Onboarding
from app.onboarding_schemas import (
    OnboardingCreate,
    OnboardingStatusUpdate,
    OnboardingResponse,
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/", response_model=OnboardingResponse, status_code=201)
def create_onboarding_task(
    payload: OnboardingCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    employee = db.get(models.Employee, payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    row = Onboarding(
        employee_id=payload.employee_id,
        task_name=payload.task_name.strip(),
        status="PENDING",
        due_date=payload.due_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=list[OnboardingResponse])
def list_onboarding_tasks(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(Onboarding)

    if user.role not in ("HR", "ADMIN"):
        employee = (
            db.query(models.Employee)
            .filter_by(user_id=user.id)
            .first()
        )
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        query = query.filter(Onboarding.employee_id == employee.id)
    elif employee_id is not None:
        query = query.filter(Onboarding.employee_id == employee_id)

    return query.order_by(
        Onboarding.due_date.asc(), Onboarding.id.asc()
    ).all()


@router.patch("/{task_id}", response_model=OnboardingResponse)
def update_onboarding_status(
    task_id: int,
    payload: OnboardingStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    row = db.get(Onboarding, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Onboarding task not found")

    if user.role not in ("HR", "ADMIN"):
        employee = (
            db.query(models.Employee)
            .filter_by(user_id=user.id)
            .first()
        )
        if not employee or employee.id != row.employee_id:
            raise HTTPException(status_code=403, detail="Not allowed to update this task")

        if payload.status != "COMPLETED":
            raise HTTPException(
                status_code=403,
                detail="Employees can only mark tasks as COMPLETED",
            )

    row.status = payload.status
    db.commit()
    db.refresh(row)
    return row
