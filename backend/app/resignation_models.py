
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Resignation(Base):
    __tablename__ = "resignations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    reason = Column(String(1000), nullable=False)
    notice_period = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
