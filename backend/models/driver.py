from sqlalchemy import Column, Integer, String, Text, Date, Boolean
from backend.db.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    license_number = Column(String(100), nullable=True)
    license_valid_until = Column(Date, nullable=True)
    note = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)