from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Trial / subscription
    trial_expires_at = Column(Date, nullable=True)
    subscription_expires_at = Column(Date, nullable=True)
    subscription_amount = Column(Float, nullable=True)   # posledná zaplatená suma €
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
