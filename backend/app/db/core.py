import os
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True)
class Db:
    engine: Engine
    session_factory: sessionmaker


def make_db(database_url: str | None = None) -> Db:
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")

    engine = create_engine(url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    return Db(engine=engine, session_factory=session_factory)


def get_session(db: Db) -> Session:
    return db.session_factory()

