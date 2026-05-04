from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool
    trial_expires_at: Optional[date] = None
    subscription_expires_at: Optional[date] = None
    subscription_amount: Optional[float] = None
    registered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class SubscriptionUpdate(BaseModel):
    trial_expires_at: Optional[date] = None
    subscription_expires_at: Optional[date] = None
    subscription_amount: Optional[float] = None
