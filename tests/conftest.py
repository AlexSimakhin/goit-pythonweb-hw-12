"""
Pytest fixtures for initializing and cleaning up the test database.
"""
import os

import dotenv
import pytest
from sqlalchemy import create_engine

from app.database import Base

ENV_TEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", ".env.test"
)
dotenv.load_dotenv(
    dotenv_path=ENV_TEST_PATH,
    override=True,
)
os.environ['TESTING'] = '1'

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before tests and drop them after tests."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
