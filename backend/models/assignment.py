from sqlalchemy import Column, Integer, Boolean, Text, Date, ForeignKey
from backend.db.database import Base


class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignments"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    assigned_from = Column(Date, nullable=True)
    assigned_to = Column(Date, nullable=True)
    is_primary = Column(Boolean, default=False)
    note = Column(Text, nullable=True)