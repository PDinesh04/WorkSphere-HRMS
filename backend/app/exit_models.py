
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class ExitManagement(Base):
    __tablename__ = "exit_management"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True
    )

    asset_return_status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    knowledge_transfer_status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    clearance_status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    exit_date = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
