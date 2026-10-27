import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent.parent / "test_vault.db"
os.environ["DATABASE_URL"] = "sqlite:///" + str(TEST_DB).replace("\\", "/")
os.environ["JWT_SECRET"] = "test_secret_not_for_production_only_for_pytest"
os.environ["PASSWORD_PEPPER"] = "test_pepper_not_for_production_only_for_pytest"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session
