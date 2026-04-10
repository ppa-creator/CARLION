from pydantic import BaseModel
from typing import Optional


class VehicleCreate(BaseModel):
    license_plate: str
    vin: Optional[str] = None
    brand: str
    model: str
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    current_km: Optional[int] = None
    note: Optional[str] = None


class VehicleRead(BaseModel):
    id: int
    license_plate: str
    vin: Optional[str] = None
    brand: str
    model: str
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    current_km: Optional[int] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}