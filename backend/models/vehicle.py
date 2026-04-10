from sqlalchemy import Column, Integer, String, Text
from backend.db.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), nullable=False, unique=True, index=True)
    vin = Column(String(50), nullable=True, unique=True)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    current_km = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)