
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app import models
from app.settlement_models import FinalSettlement
from app.settlement_schemas import (
    FinalSettlementCreate,
    FinalSettlementStatusUpdate,
    FinalSettlementResponse,
)

router = APIRouter(
    prefix="/settlements",
    tags=["Final Settlements"],
)


@router.post("/", response_model=FinalSettlementResponse, status_code=201)
def create_settlement(
    data: FinalSettlementCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    employee = db.query(models.Employee).filter(
        models.Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = db.query(FinalSettlement).filter(
        FinalSettlement.employee_id == data.employee_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A settlement already exists for this employee",
        )

    net_payable = (
        data.pending_salary
        + data.bonus
        + data.leave_encashment
        - data.deductions
    )

    if net_payable < 0:
        raise HTTPException(
            status_code=400,
            detail="Deductions cannot exceed the total payable amount",
        )

    settlement = FinalSettlement(
        employee_id=data.employee_id,
        pending_salary=data.pending_salary,
        bonus=data.bonus,
        leave_encashment=data.leave_encashment,
        deductions=data.deductions,
        net_payable=net_payable,
        status="PENDING",
    )

    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/", response_model=list[FinalSettlementResponse])
def list_settlements(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    return db.query(FinalSettlement).order_by(
        FinalSettlement.created_at.desc()
    ).all()


@router.patch("/{settlement_id}/status", response_model=FinalSettlementResponse)
def update_settlement_status(
    settlement_id: int,
    data: FinalSettlementStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    settlement = db.get(FinalSettlement, settlement_id)

    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    if settlement.status == "PAID":
        raise HTTPException(
            status_code=409,
            detail="Settlement has already been paid",
        )

    settlement.status = data.status
    db.commit()
    db.refresh(settlement)
    return settlement

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app import models
from app.settlement_models import FinalSettlement
from app.settlement_schemas import (
    FinalSettlementCreate,
    FinalSettlementStatusUpdate,
    FinalSettlementResponse,
)

router = APIRouter(
    prefix="/settlements",
    tags=["Final Settlements"],
)


@router.post("/", response_model=FinalSettlementResponse, status_code=201)
def create_settlement(
    data: FinalSettlementCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    employee = db.query(models.Employee).filter(
        models.Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = db.query(FinalSettlement).filter(
        FinalSettlement.employee_id == data.employee_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A settlement already exists for this employee",
        )

    net_payable = (
        data.pending_salary
        + data.bonus
        + data.leave_encashment
        - data.deductions
    )

    if net_payable < 0:
        raise HTTPException(
            status_code=400,
            detail="Deductions cannot exceed the total payable amount",
        )

    settlement = FinalSettlement(
        employee_id=data.employee_id,
        pending_salary=data.pending_salary,
        bonus=data.bonus,
        leave_encashment=data.leave_encashment,
        deductions=data.deductions,
        net_payable=net_payable,
        status="PENDING",
    )

    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/", response_model=list[FinalSettlementResponse])
def list_settlements(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    return db.query(FinalSettlement).order_by(
        FinalSettlement.created_at.desc()
    ).all()


@router.patch("/{settlement_id}/status", response_model=FinalSettlementResponse)
def update_settlement_status(
    settlement_id: int,
    data: FinalSettlementStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("HR", "ADMIN")),
):
    settlement = db.get(FinalSettlement, settlement_id)

    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    if settlement.status == "PAID":
        raise HTTPException(
            status_code=409,
            detail="Settlement has already been paid",
        )

    settlement.status = data.status
    db.commit()
    db.refresh(settlement)
    return settlement
