from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Determine database URL (fallback to local SQLite)
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./comparison.db"

# SQLite needs special connect_args
_engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()


def init_db() -> None:
    """Import models and create tables if they do not exist."""
    # Import models to register them with SQLAlchemy's metadata
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


# Initialize database on first import
init_db() 