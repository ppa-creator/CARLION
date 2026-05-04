from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text

from backend.db.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    trip_date = Column(Date, nullable=False)
    start_km = Column(Integer, nullable=True)
    end_km = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    route = Column(String(255), nullable=True)
    route_from = Column(String(255), nullable=True)
    route_to = Column(String(255), nullable=True)
    purpose = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
