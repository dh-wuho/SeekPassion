import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from seekpassion_api.db import Base, get_db
from seekpassion_api.main import app
from seekpassion_api.models import AuthProvider, Company, User


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def demo_user(db_session: Session) -> User:
    user = User(id=uuid.uuid4(), email="demo@example.com", auth_provider=AuthProvider.email)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def demo_company(db_session: Session) -> Company:
    company = Company(
        name="Anthropic",
        career_url="https://boards.greenhouse.io/anthropic",
        ats_type="greenhouse",
    )
    db_session.add(company)
    db_session.commit()
    return company
