"""Tests for user CRUD and auth operations.

Uses in-memory SQLite and pytest fixtures.
"""
# pylint: disable=redefined-outer-name

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.schemas.user import UserCreate
from app.crud.user import create_user, authenticate_user, verify_user_email, update_avatar
from app.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def session():
    """Provide a transactional database session for each test."""
    Base.metadata.create_all(bind=engine)
    _session = TestingSessionLocal()
    try:
        yield _session
    finally:
        _session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user(session):
    """Should create a user with hashed password."""
    user_in = UserCreate(username="testuser", email="test@example.com", password="password123")
    user = create_user(session, user_in)
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password != "password123"


def test_create_user_duplicate_email(session):
    """Should raise HTTPException with 409 when email is duplicated."""
    user_in = UserCreate(username="user1", email="dup@example.com", password="pass1")
    create_user(session, user_in)
    # Current implementation raises HTTPException with 409 on duplicate email
    with pytest.raises(HTTPException) as exc:
        create_user(session, user_in)
    assert exc.value.status_code == 409


def test_authenticate_user(session):
    """Should authenticate with valid credentials and fail otherwise."""
    user_in = UserCreate(username="authuser", email="auth@example.com", password="secret")
    create_user(session, user_in)
    user = authenticate_user(session, "authuser", "secret")
    assert user is not None
    assert user.username == "authuser"
    with pytest.raises(HTTPException):
        _ = authenticate_user(session, "authuser", "wrongpass")


def test_verify_user_email(session):
    """Should set is_verified to True."""
    user_in = UserCreate(username="verifyuser", email="verify@example.com", password="pass")
    user = create_user(session, user_in)
    assert not user.is_verified
    user = verify_user_email(session, user.id)
    assert user.is_verified


def test_update_avatar(session):
    """Should update avatar_url field."""
    user_in = UserCreate(username="avataruser", email="avatar@example.com", password="pass")
    user = create_user(session, user_in)
    user = update_avatar(session, user.id, "http://example.com/avatar.png")
    assert user.avatar_url == "http://example.com/avatar.png"
