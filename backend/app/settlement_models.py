
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class FinalSettlement(Base):
    __tablename__ = "final_settlements"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True
    )

    pending_salary = Column(Float, nullable=False, default=0)
    bonus = Column(Float, nullable=False, default=0)
    leave_encashment = Column(Float, nullable=False, default=0)
    deductions = Column(Float, nullable=False, default=0)
    net_payable = Column(Float, nullable=False, default=0)

    status = Column(String(20), nullable=False, default="PENDING")

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
