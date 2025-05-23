# File: app/db/base.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
# Add connect_args for SQLite (only needed for SQLite)
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()