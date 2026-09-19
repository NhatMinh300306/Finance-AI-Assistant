"""
Shared test fixtures and configuration.
Uses an in-memory SQLite database for test isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.db.models import User
from app.main import app

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=test_engine)
    # Create default user
    db = TestSessionLocal()
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Test User", email="test@finmate.app")
        db.add(user)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Direct database session for service-level tests."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
