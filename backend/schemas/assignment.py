from pydantic import BaseModel
from typing import Optional
from datetime import date


class AssignmentCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    assigned_from: Optional[date] = None
    assigned_to: Optional[date] = None
    is_primary: bool = False
    note: Optional[str] = None


class AssignmentRead(BaseModel):
    id: int
    driver_id: int
    vehicle_id: int
    assigned_from: Optional[date] = None
    assigned_to: Optional[date] = None
    is_primary: bool
    note: Optional[str] = None

    model_config = {"from_attributes": True}