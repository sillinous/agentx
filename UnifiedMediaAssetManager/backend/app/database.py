import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from .models.database import Base

# Use environment variable or default to local SQLite file
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sql_app.db")

# module logger
logger = logging.getLogger(__name__)


def _create_engine(database_url: str):
    """Create SQLAlchemy engine with appropriate settings for the database type."""
    is_sqlite = database_url.startswith("sqlite")
    is_testing = database_url == "sqlite:///:memory:"

    if is_sqlite:
        # SQLite-specific configuration
        connect_args = {"check_same_thread": False}
        if is_testing:
            # For in-memory SQLite, use StaticPool to share connection across threads
            return create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool
            )
        return create_engine(database_url, connect_args=connect_args)
    else:
        # PostgreSQL/other databases
        # Use connection pooling for production
        return create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Verify connection health before use
        )


engine = _create_engine(DATABASE_URL)
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
