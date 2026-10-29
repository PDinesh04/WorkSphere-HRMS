
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict


class ExitManagementCreate(BaseModel):
    employee_id: int


class ExitManagementUpdate(BaseModel):
    asset_return_status: Optional[
        Literal["PENDING", "COMPLETED"]
    ] = None

    knowledge_transfer_status: Optional[
        Literal["PENDING", "COMPLETED"]
    ] = None

    clearance_status: Optional[
        Literal["PENDING", "COMPLETED"]
    ] = None

    exit_date: Optional[datetime] = None


class ExitManagementResponse(BaseModel):
    id: int
    employee_id: int
    asset_return_status: str
    knowledge_transfer_status: str
    clearance_status: str
    exit_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
