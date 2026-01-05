import os
import tempfile

# Ensure tests use a separate, deterministic SQLite file before any app imports
# This file is loaded by pytest before test modules, so set DATABASE_URL early.
_test_db_fd, _test_db_path = tempfile.mkstemp(prefix="umam_test_", suffix=".db")
try:
    os.close(_test_db_fd)
except Exception:
    pass
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_test_db_path}")

# Import and initialize the application's canonical DB reset routine
try:
    from app.database import create_db_and_tables
    create_db_and_tables()
except Exception:
    # If initialization fails, let tests handle/report the error rather than crashing import
    pass

# Provide a fixture that yields the DB path for potential cleanup or introspection
import pytest

@pytest.fixture(scope="session")
def test_db_path():
    return _test_db_path

@pytest.fixture(autouse=True)
def ensure_clean_db_for_test(test_db_path):
    # For each test, ensure the DB reflects the latest schema (no data isolation per-test here)
    try:
        from app.database import create_db_and_tables
        create_db_and_tables()
    except Exception:
        pass
    yield
