import os

import pytest
from sqlalchemy import text

from app import create_app
from app.db.core import get_session


@pytest.fixture(scope="session", autouse=True)
def _assert_database_url_set():
    # Tests expect to run with Postgres via docker compose.
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be set for tests")


@pytest.fixture()
def app():
    app = create_app()
    app.testing = True
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_db(app):
    db = app.config["db"]
    session = get_session(db)
    try:
        # Deterministic cleanup between tests.
        session.execute(text("TRUNCATE TABLE stock_movements RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE"))
        session.commit()
        yield
    finally:
        session.close()

