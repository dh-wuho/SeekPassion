from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from seekpassion.db.models import Base

_SessionLocal: sessionmaker[Session] | None = None


def init_db(db_path: str | Path = "seekpassion.db") -> None:
    global _SessionLocal
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    _SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    if _SessionLocal is None:
        raise RuntimeError("DB not initialised — call init_db() first")
    return _SessionLocal()
