import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.database import Base

DATABASE_URL = "sqlite:///./sql_app.db"

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
    # For tests and development, remove any stale sqlite file then recreate schema.
    # This ensures we start from a clean state and avoid schema drift.
    try:
        logger.info("create_db_and_tables: DATABASE_URL=%s", DATABASE_URL)
        # If using sqlite file, prefer removing the file to avoid low-level sqlite errors
        if DATABASE_URL.startswith("sqlite:///"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            try:
                abs_db_path = os.path.abspath(db_path)
                if os.path.exists(db_path):
                    logger.info("Removing sqlite file to reset DB: %s", abs_db_path)
                    os.remove(db_path)
            except Exception:
                logger.exception("Failed to remove sqlite file %s", db_path)

        # Create schema (will create a new sqlite file if removed above)
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema created successfully.")
    except Exception as exc:
        logger.exception("Error creating database schema: %s", exc)
