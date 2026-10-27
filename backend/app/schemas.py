from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)

class LoginIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class EmployeeIn(BaseModel):
    user_id: int
    full_name: str
    designation: str = ""
    department: str = ""
    joining_date: date | None = None
    salary: float = Field(default=0, ge=0)
    status: str = "ACTIVE"

class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    designation: str | None = None
    department: str | None = None
    joining_date: date | None = None
    salary: float | None = Field(default=None, ge=0)
    status: str | None = None

class LeaveIn(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = Field(min_length=2, max_length=2000)

class LeaveDecision(BaseModel):
    status: str

class PayrollIn(BaseModel):
    employee_id: int
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    basic_salary: float = Field(ge=0)
    allowances: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)
    bonus: float = Field(default=0, ge=0)

class PolicyIn(BaseModel):
    leave_type: str
    total_days_allowed: int = Field(ge=0, le=365)

class RoleUpdate(BaseModel):
    role: str
    is_active: bool = True


class ShiftIn(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

class EmployeeShiftIn(BaseModel):
    employee_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)

class PerformanceIn(BaseModel):
    employee_id: int = Field(gt=0)
    review_period: str = Field(min_length=3, max_length=80)
    rating: int = Field(ge=1, le=5)
    feedback: str = Field(min_length=2, max_length=5000)
