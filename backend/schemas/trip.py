from datetime import date
from typing import Optional

from pydantic import BaseModel


class TripCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    trip_date: date
    start_km: Optional[int] = None
    end_km: Optional[int] = None
    distance_km: Optional[float] = None
    route: Optional[str] = None
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    purpose: Optional[str] = None
    note: Optional[str] = None


class TripRead(BaseModel):
    id: int
    driver_id: int
    vehicle_id: int
    trip_date: date
    start_km: Optional[int] = None
    end_km: Optional[int] = None
    distance_km: Optional[float] = None
    route: Optional[str] = None
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    purpose: Optional[str] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}
