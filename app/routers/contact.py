"""
FastAPI router for managing contact endpoints.
Implements RESTful routes for CRUD operations, search, and upcoming birthdays.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.contact import ContactCreate, ContactUpdate, ContactOut
from app.crud.contact import create_contact, get_contacts, get_contact, update_contact, delete_contact, search_contacts, get_upcoming_birthdays

router = APIRouter(prefix="/contacts", tags=["contacts"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_db():
    """Provide a SQLAlchemy session for request lifecycle.

    Yields:
        Session: Database session that is closed after request is handled.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ContactOut)
async def create_contact_route(contact: ContactCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Create a new contact for the authenticated user.

    Args:
        contact: Contact payload.
        token: Bearer access token.
        db: SQLAlchemy session.
    """
    return create_contact(db, contact, token)


@router.get("/", response_model=List[ContactOut])
async def list_contacts(skip: int = 0, limit: int = 100, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """List contacts with pagination."""
    return get_contacts(db, skip=skip, limit=limit, token=token)


@router.get("/search", response_model=List[ContactOut])
async def search_contacts_route(q: str = Query(..., min_length=1, description="Search query"), token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Search contacts by name, email or phone."""
    return search_contacts(db, q, token)


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact_route(contact_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Retrieve a single contact by id."""
    return get_contact(db, contact_id, token)


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact_route(contact_id: int, contact: ContactUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Update an existing contact."""
    return update_contact(db, contact_id, contact, token)


@router.delete("/{contact_id}", response_model=bool)
async def delete_contact_route(contact_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Delete a contact by id."""
    return delete_contact(db, contact_id, token)


@router.get("/birthdays/upcoming", response_model=List[ContactOut])
async def upcoming_birthdays_route(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get contacts with birthdays in the next 7 days."""
    return get_upcoming_birthdays(db, token)
