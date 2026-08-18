"""Test setup shared by all PratikAI tests.

Points the app at an isolated SQLite file so tests never touch the real
data/database/pratikai.db. Must run before any `app.*` module is imported,
since app.db.database builds its engine at import time from get_settings().
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_DB_PATH = ROOT / "data" / "database" / "test_pratikai.db"
os.environ["PRATIKAI_DATABASE__PATH"] = str(TEST_DB_PATH)

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    from app.db.base import Base
    from app.db.database import engine
    from app.db import models  # noqa: F401  registers tables on Base.metadata

    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # A prior run's file can survive teardown (e.g. a lingering Windows file
    # handle blocks unlink()); start every session from a guaranteed-empty
    # schema rather than trusting create_all() alone, since it won't clear
    # stale rows from an old run and those collide on unique constraints.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except PermissionError:
        pass
