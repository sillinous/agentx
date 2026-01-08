import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.database import Base

# Use environment variable or default to local SQLite file
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sql_app.db")

# module logger
logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    """Create database tables if they don't exist."""
    try:
        logger.info("create_db_and_tables: DATABASE_URL=%s", DATABASE_URL)
        # Create schema - SQLAlchemy will only create tables that don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema created/verified successfully.")
    except Exception as exc:
        logger.exception("Error creating database schema: %s", exc)
