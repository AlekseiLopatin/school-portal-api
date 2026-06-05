"""
SQLAlchemy engine and session setup.

We use SQLite for development — it's a single file (school_portal.db) that lives
in the project directory. No separate database server needed. For production you
would swap the connection string to PostgreSQL and remove the check_same_thread
argument (which is a SQLite-specific concession for FastAPI's threaded request
handling).
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./school_portal.db")

# Postgres-on-Railway sometimes hands out "postgres://..." which SQLAlchemy 2.0 doesn't accept
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread is only needed for SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models inherit from
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency-injectable database session.

    FastAPI calls this via Depends() for each incoming request: it opens a
    session, yields it to the path-operation function, and closes the session
    after the response is sent — even if an exception is raised mid-handler.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
