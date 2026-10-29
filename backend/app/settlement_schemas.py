
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class FinalSettlementCreate(BaseModel):
    employee_id: int = Field(gt=0)
    pending_salary: float = Field(ge=0)
    bonus: float = Field(ge=0)
    leave_encashment: float = Field(ge=0)
    deductions: float = Field(ge=0)


class FinalSettlementStatusUpdate(BaseModel):
    status: Literal["APPROVED", "PAID"]


class FinalSettlementResponse(BaseModel):
    id: int
    employee_id: int
    pending_salary: float
    bonus: float
    leave_encashment: float
    deductions: float
    net_payable: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
