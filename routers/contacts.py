"""
FastAPI router for managing contact endpoints.
Implements RESTful routes for CRUD operations, search, and upcoming birthdays.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import ContactCreate, ContactUpdate, ContactOut
import crud

router = APIRouter(prefix="/contacts", tags=["contacts"])

def get_db():
    """
    Dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ContactOut)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """
    Create a new contact.
    """
    return crud.create_contact(db, contact)

@router.get("/", response_model=List[ContactOut])
async def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all contacts with pagination.
    """
    return crud.get_contacts(db, skip, limit)

@router.get("/{contact_id}", response_model=ContactOut)
async def read_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a contact by its ID.
    """
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)):
    """
    Update an existing contact by its ID.
    """
    db_contact = crud.update_contact(db, contact_id, contact)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}", response_model=ContactOut)
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Delete a contact by its ID.
    """
    db_contact = crud.delete_contact(db, contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search/", response_model=List[ContactOut])
async def search_contacts(
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Search contacts by first name, last name, or email.
    """
    return crud.search_contacts(db, first_name, last_name, email)

@router.get("/birthdays/upcoming", response_model=List[ContactOut])
async def get_upcoming_birthdays(db: Session = Depends(get_db)):
    """
    Get contacts with birthdays in the next 7 days.
    """
    return crud.upcoming_birthdays(db)
