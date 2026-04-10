from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class DriverCreate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    license_number: Optional[str] = None
    license_valid_until: Optional[date] = None
    note: Optional[str] = None


class DriverRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    license_number: Optional[str] = None
    license_valid_until: Optional[date] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}