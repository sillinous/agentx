from typing import Iterator
from sqlmodel import SQLModel, create_engine, Session
import os

# Use a local SQLite file for development. Override with DATABASE_URL env var for production.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sql_app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})


def init_db() -> None:
    # Prefer the canonical initializer so all entrypoints share the same
    # deterministic reset behavior during development and testing.
    try:
        from .database import create_db_and_tables

        create_db_and_tables()
    except Exception:
        SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
