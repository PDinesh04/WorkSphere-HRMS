
from datetime import time
from pydantic import BaseModel, ConfigDict, EmailStr


class CompanySettingCreate(BaseModel):
    company_name: str = "WorkSphere"
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    working_hours_start: time | None = None
    working_hours_end: time | None = None
    weekly_holidays: str = "Saturday,Sunday"


class CompanySettingResponse(CompanySettingCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
