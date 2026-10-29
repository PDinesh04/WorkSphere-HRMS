from datetime import datetime, date
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="EMPLOYEE")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    employee = relationship("Employee", back_populates="user", uselist=False)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(160), nullable=False)
    designation = Column(String(120), default="")
    department = Column(String(120), default="")
    joining_date = Column(Date, default=date.today)
    salary = Column(Float, default=0)
    status = Column(String(20), default="ACTIVE")
    user = relationship("User", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date = Column(Date, default=date.today, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    status = Column(String(20), default="PRESENT")
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),)

class LeavePolicy(Base):
    __tablename__ = "leave_policies"
    id = Column(Integer, primary_key=True, index=True)
    leave_type = Column(String(20), unique=True, nullable=False)
    total_days_allowed = Column(Integer, default=12, nullable=False)

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    remaining_days = Column(Integer, default=12, nullable=False)
    __table_args__ = (UniqueConstraint("employee_id", "leave_type", name="uq_balance_employee_type"),)

class LeaveRequest(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Payroll(Base):
    __tablename__ = "payroll"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    basic_salary = Column(Float, default=0, nullable=False)
    allowances = Column(Float, default=0, nullable=False)
    deductions = Column(Float, default=0, nullable=False)
    bonus = Column(Float, default=0, nullable=False)
    net_salary = Column(Float, default=0, nullable=False)
    month = Column(String(7), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("employee_id", "month", name="uq_payroll_employee_month"),)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(40), unique=True, nullable=False)
    start_time = Column(String(5), nullable=False)  # HH:MM local time
    end_time = Column(String(5), nullable=False)

class EmployeeShift(Base):
    __tablename__ = "employee_shifts"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("employee_id", name="uq_employee_shift_employee"),)

class EmployeeDocument(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), unique=True, nullable=False)
    file_url = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class PerformanceReview(Base):
    __tablename__ = "performance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    review_period = Column(String(80), nullable=False)
    rating = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
