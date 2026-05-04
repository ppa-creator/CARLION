from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from backend.db.database import Base


class UserEmail(Base):
    __tablename__ = "user_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    verified_at = Column(DateTime, default=datetime.utcnow, nullable=False)
