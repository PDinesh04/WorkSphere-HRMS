
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_current_user, require_roles
from app.settings_models import CompanySetting
from app.settings_schemas import (
    CompanySettingCreate,
    CompanySettingResponse,
)

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("/company", response_model=CompanySettingResponse)
def get_company_settings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settings = db.query(CompanySetting).first()

    if not settings:
        settings = CompanySetting()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.put(
    "/company",
    response_model=CompanySettingResponse,
)
def update_company_settings(
    payload: CompanySettingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN")),
):
    settings = db.query(CompanySetting).first()

    if not settings:
        settings = CompanySetting()
        db.add(settings)

    for field, value in payload.model_dump().items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings
