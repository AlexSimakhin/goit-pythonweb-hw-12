"""
CRUD operations for managing contacts in the database.
Implements create, read, update, delete, search, and upcoming birthdays logic.
"""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Contact
from schemas import ContactCreate, ContactUpdate

def create_contact(db: Session, contact: ContactCreate) -> Contact:
    """
    Create a new contact in the database.
    """
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, skip: int = 0, limit: int = 100) -> List[Contact]:
    """
    Retrieve a list of all contacts with pagination.
    """
    return db.query(Contact).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int) -> Optional[Contact]:
    """
    Retrieve a single contact by its ID.
    """
    return db.query(Contact).filter(Contact.id == contact_id).first()

def update_contact(db: Session, contact_id: int, contact: ContactUpdate) -> Optional[Contact]:
    """
    Update an existing contact by its ID.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int) -> Optional[Contact]:
    """
    Delete a contact by its ID.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, first_name: Optional[str], last_name: Optional[str], email: Optional[str]) -> List[Contact]:
    """
    Search contacts by first name, last name, or email.
    """
    query = db.query(Contact)
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    return query.all()

def upcoming_birthdays(db: Session) -> List[Contact]:
    """
    Get contacts with birthdays in the next 7 days.
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(Contact.birthday.between(today, next_week)).all()
