from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class RefuelCreate(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    refuel_date: date
    refuel_time: Optional[time] = None
    liters: float
    total_cost: float
    price_per_liter: Optional[float] = None
    odometer_km: Optional[int] = None
    station: Optional[str] = None
    fuel_type: Optional[str] = None
    note: Optional[str] = None
    trip_id: Optional[int] = None


class RefuelRead(BaseModel):
    id: int
    vehicle_id: int
    driver_id: Optional[int] = None
    refuel_date: date
    refuel_time: Optional[time] = None
    liters: float
    total_cost: float
    price_per_liter: Optional[float] = None
    odometer_km: Optional[int] = None
    station: Optional[str] = None
    fuel_type: Optional[str] = None
    note: Optional[str] = None
    trip_id: Optional[int] = None

    model_config = {"from_attributes": True}
