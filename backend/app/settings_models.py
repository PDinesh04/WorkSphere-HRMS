
from sqlalchemy import Column, Integer, String, Time
from app.database import Base


class CompanySetting(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), nullable=False, default="WorkSphere")
    email = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(300), nullable=True)
    working_hours_start = Column(Time, nullable=True)
    working_hours_end = Column(Time, nullable=True)
    weekly_holidays = Column(String(100), default="Saturday,Sunday")
