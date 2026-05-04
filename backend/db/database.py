import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_raw_url = os.environ.get("DATABASE_URL", "sqlite:///./carlion.db")

# Railway PostgreSQL uses postgres:// scheme, SQLAlchemy needs postgresql://
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()