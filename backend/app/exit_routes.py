
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app.models import User
from app import models
from app.exit_models import ExitManagement
from app.exit_schemas import (
    ExitManagementCreate,
    ExitManagementUpdate,
    ExitManagementResponse,
)

router = APIRouter(prefix="/exit-management", tags=["Exit Management"])


@router.post("/", response_model=ExitManagementResponse, status_code=201)
def create_exit_record(
    data: ExitManagementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("HR", "ADMIN")),
):
    employee = db.query(models.Employee).filter(
        models.Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = db.query(ExitManagement).filter(
        ExitManagement.employee_id == data.employee_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Exit record already exists for this employee",
        )

    record = ExitManagement(employee_id=data.employee_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[ExitManagementResponse])
def list_exit_records(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("HR", "ADMIN")),
):
    return db.query(ExitManagement).order_by(
        ExitManagement.id.desc()
    ).all()


@router.patch("/{record_id}", response_model=ExitManagementResponse)
def update_exit_record(
    record_id: int,
    data: ExitManagementUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("HR", "ADMIN")),
):
    record = db.query(ExitManagement).filter(
        ExitManagement.id == record_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Exit record not found")

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record
