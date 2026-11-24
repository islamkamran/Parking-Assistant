"""Tests run against a throwaway SQLite database, never your MySQL data.

get_db is overridden so every request in a test uses the test database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401  (register all tables)
from app.db.models import Fine
from app.db.setup import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add_all([
            Fine(fine_id="F-1001", plate="A12345", amount_aed=150, reason="Parking time expired"),
            Fine(fine_id="F-1002", plate="A12345", amount_aed=200, reason="No parking ticket displayed"),
            Fine(fine_id="F-2001", plate="D54321", amount_aed=500, reason="Parked in a disabled bay"),
        ])
        db.commit()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
