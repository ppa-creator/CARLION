from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text, Time

from backend.db.database import Base


class Refuel(Base):
    __tablename__ = "refuels"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    refuel_date = Column(Date, nullable=False)
    refuel_time = Column(Time, nullable=True)
    liters = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=True)
    odometer_km = Column(Integer, nullable=True)
    station = Column(String(255), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
