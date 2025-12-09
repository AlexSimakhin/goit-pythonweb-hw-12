"""Tests for contact CRUD operations and helpers.

This module uses pytest fixtures and in-memory SQLite to validate CRUD behavior.
"""
# pylint: disable=redefined-outer-name

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.schemas.contact import ContactCreate, ContactUpdate
from app.crud.contact import (
    create_contact,
    get_contacts,
    get_contact,
    update_contact,
    delete_contact,
    search_contacts,
    get_upcoming_birthdays,
)
from app.database import Base
from app.utils.auth import create_access_token

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


@pytest.fixture
def user_token():
    """Return a signed access token for a dummy user (id=1)."""
    return create_access_token({"user_id": 1})


@pytest.fixture
def contact_data():
    """Provide a sample contact payload for creating records."""
    return ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        birthday=date.today(),
        extra="Test extra",
    )


def test_create_contact(session, user_token, contact_data):
    """Should create a contact owned by the user."""
    contact = create_contact(session, contact_data, user_token)
    assert contact.first_name == "John"
    assert contact.user_id == 1


def test_get_contacts(session, user_token, contact_data):
    """Should return a list with the created contact."""
    create_contact(session, contact_data, user_token)
    contacts = get_contacts(session, token=user_token)
    assert len(contacts) == 1


def test_get_contact(session, user_token, contact_data):
    """Should retrieve the contact by id."""
    contact = create_contact(session, contact_data, user_token)
    found = get_contact(session, contact.id, user_token)
    assert found.id == contact.id


def test_update_contact(session, user_token, contact_data):
    """Should update fields of an existing contact."""
    contact = create_contact(session, contact_data, user_token)
    data = contact_data.model_dump()
    data.pop("user_id", None)
    data["phone"] = "9876543210"
    update = ContactUpdate(**data)
    updated = update_contact(session, contact.id, update, user_token)
    assert updated.phone == "9876543210"


def test_delete_contact(session, user_token, contact_data):
    """Should delete contact and no longer find it afterwards."""
    contact = create_contact(session, contact_data, user_token)
    deleted = delete_contact(session, contact.id, user_token)
    assert deleted is True
    
    with pytest.raises(HTTPException):
        _ = get_contact(session, contact.id, user_token)


def test_search_contacts(session, user_token, contact_data):
    """Should find a contact by a matching query and none otherwise."""
    create_contact(session, contact_data, user_token)
    results = search_contacts(session, "John", user_token)
    assert len(results) == 1
    results = search_contacts(session, "NotExist", user_token)
    assert len(results) == 0


def test_get_upcoming_birthdays(session, user_token):
    """Should include a contact with birthday within next 7 days."""
    today = date.today()
    contact = ContactCreate(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone="5555555555",
        birthday=today + timedelta(days=3),
        extra="",
    )
    create_contact(session, contact, user_token)
    upcoming = get_upcoming_birthdays(session, user_token)
    assert len(upcoming) >= 1
