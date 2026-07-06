from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import get_settings


@lru_cache
def _engine() -> object:
    settings = get_settings()
    return create_engine(settings.database_url, connect_args={"check_same_thread": False})


def _session_factory() -> sessionmaker[Session]:  # type: ignore[type-arg]
    from sqlalchemy import Engine

    engine = _engine()
    assert isinstance(engine, Engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    factory = _session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    from sqlalchemy import Engine

    from backend.db import models  # noqa: F401 — registers all ORM classes

    engine = _engine()
    assert isinstance(engine, Engine)
    from backend.db.base import Base

    Base.metadata.create_all(bind=engine)
