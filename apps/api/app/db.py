"""SQLAlchemy engine/session setup."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings


class Base(DeclarativeBase):
    """Base for all API-owned ORM models."""


_engine: Engine | None = None


def get_engine() -> Engine:
    """Create the engine on first use.

    Lazy so that importing pure modules (scoring, selection) doesn't require the
    DB driver to be installed or a database to be reachable — keeps unit tests
    and tooling lightweight.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True, future=True)
    return _engine


def SessionLocal() -> Session:
    """Construct a new DB session bound to the lazily-created engine."""
    return Session(bind=get_engine(), autoflush=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
