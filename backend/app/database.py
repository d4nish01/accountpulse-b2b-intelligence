"""Database setup.

Uses PostgreSQL when DATABASE_URL is set (e.g. in docker-compose),
otherwise falls back to a local SQLite file so the project runs with
zero setup: `uvicorn app.main:app` just works.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./accountpulse.db")

# check_same_thread is a SQLite-only setting; PostgreSQL ignores it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: one DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
