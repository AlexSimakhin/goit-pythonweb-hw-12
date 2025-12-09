"""
CRUD operations for managing contacts in the database.
Implements create, read, update, delete, search, and upcoming birthdays logic.
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate
from app.utils.auth import decode_access_token


def _get_user_id(token: str) -> int:
    """Extract and validate the current user id from a JWT access token.

    Parameters
    ----------
    token : str
        Bearer JWT access token provided by the client.

    Returns
    -------
    int
        The authenticated user's id.

    Raises
    ------
    HTTPException
        If the token is missing or invalid, or if the payload lacks a user_id.
    """
    payload = decode_access_token(token) if token else None
    if not payload or not payload.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
        )
    return int(payload["user_id"])  # enforce int


def create_contact(db: Session, contact: ContactCreate, token: str) -> Contact:
    """Create a new contact owned by the authenticated user.

    Parameters
    ----------
    db : Session
        SQLAlchemy database session.
    contact : ContactCreate
        Validated contact data to be persisted.
    token : str
        Bearer JWT access token of the current user.

    Returns
    -------
    Contact
        The newly created contact ORM instance.

    Raises
    ------
    HTTPException
        If a contact with the same email already exists for the user.
    """
    user_id = _get_user_id(token)
    # Ensure unique email per system (or per user depending on requirements)
    existing = db.query(Contact).filter(Contact.email == contact.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists",
        )

    obj = Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        extra=contact.extra,
        user_id=user_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_contacts(db: Session, skip: int = 0, limit: int = 100, token: str = None) -> List[Contact]:
    """List contacts for the authenticated user with pagination.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    skip : int, optional
        Number of records to skip (offset), by default 0.
    limit : int, optional
        Maximum number of records to return, by default 100.
    token : str, optional
        JWT access token. If omitted, raises 401.

    Returns
    -------
    List[Contact]
        A list of contacts belonging to the current user.
    """
    user_id = _get_user_id(token)
    return (
        db.query(Contact)
        .filter(Contact.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_contact(db: Session, contact_id: int, token: str = None) -> Optional[Contact]:
    """Retrieve a single contact by id ensuring ownership.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    contact_id : int
        Primary key of the contact.
    token : str, optional
        JWT access token.

    Returns
    -------
    Optional[Contact]
        The contact if found and owned by the user, otherwise raises 404.

    Raises
    ------
    HTTPException
        If the contact does not exist or is not owned by the user.
    """
    user_id = _get_user_id(token)
    obj = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return obj


def update_contact(db: Session, contact_id: int, contact: ContactUpdate, token: str = None) -> Optional[Contact]:
    """Update an existing contact owned by the current user.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    contact_id : int
        Contact id.
    contact : ContactUpdate
        New values for the contact.
    token : str, optional
        JWT access token.

    Returns
    -------
    Optional[Contact]
        The updated contact instance.

    Raises
    ------
    HTTPException
        If the contact is not found or not owned by the user.
    """
    user_id = _get_user_id(token)
    obj = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    # Apply updates
    obj.first_name = contact.first_name
    obj.last_name = contact.last_name
    obj.email = contact.email
    obj.phone = contact.phone
    obj.birthday = contact.birthday
    obj.extra = contact.extra
    db.commit()
    db.refresh(obj)
    return obj


def delete_contact(db: Session, contact_id: int, token: str = None) -> bool:
    """Delete a contact owned by the current user.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    contact_id : int
        Contact id to delete.
    token : str, optional
        JWT access token.

    Returns
    -------
    bool
        True if deletion succeeded.

    Raises
    ------
    HTTPException
        If the contact does not exist or is not owned by the user.
    """
    user_id = _get_user_id(token)
    obj = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(obj)
    db.commit()
    return True


def search_contacts(db: Session, query: str, token: str = None) -> List[Contact]:
    """Search contacts by first name, last name, email, or phone for the current user.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    query : str
        Case-insensitive search term.
    token : str, optional
        JWT access token.

    Returns
    -------
    List[Contact]
        Matching contacts owned by the user.
    """
    user_id = _get_user_id(token)
    q = f"%{query}%"
    return (
        db.query(Contact)
        .filter(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(q),
                Contact.last_name.ilike(q),
                Contact.email.ilike(q),
                Contact.phone.ilike(q),
            ),
        )
        .all()
    )


def get_upcoming_birthdays(db: Session, token: str = None) -> List[Contact]:
    """Get contacts whose birthdays fall within the next 7 days.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    token : str, optional
        JWT access token.

    Returns
    -------
    List[Contact]
        Contacts with birthdays in the upcoming week.
    """
    user_id = _get_user_id(token)
    today = date.today()
    next_week = today + timedelta(days=7)

    # Compare month/day portion. For simplicity with SQLite, filter by range in year
    # and refine in Python if necessary.
    results = db.query(Contact).filter(Contact.user_id == user_id).all()

    def _is_upcoming(bday: date) -> bool:
        # Normalize year to current for comparison by month/day
        try:
            normalized = date(today.year, bday.month, bday.day)
        except ValueError:
            # Handle Feb 29 in non-leap years: treat as Mar 1
            normalized = date(today.year, 3, 1)
        return today <= normalized <= next_week

    return [c for c in results if _is_upcoming(c.birthday)]
