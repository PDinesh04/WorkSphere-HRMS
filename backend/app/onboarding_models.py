from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base


class Onboarding(Base):
    __tablename__ = "onboarding"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    task_name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    due_date = Column(Date, nullable=True)