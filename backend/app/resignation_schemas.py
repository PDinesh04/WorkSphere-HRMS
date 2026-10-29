from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ResignationCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
    notice_period: int = Field(ge=0, le=365)


class ResignationStatusUpdate(BaseModel):
    status: Literal["APPROVED", "REJECTED"]


class ResignationResponse(BaseModel):
    id: int
    employee_id: int
    reason: str
    notice_period: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)