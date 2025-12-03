"""
Pydantic schemas for validating and serializing contact data.
Defines base, create, update, and output schemas for contacts.
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field

class ContactBase(BaseModel):
    """
    Base schema for contact data validation.
    """
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    email: EmailStr
    phone: str
    birthday: date
    extra: Optional[str] = None

class ContactCreate(ContactBase):
    """
    Schema for creating a new contact.
    """

class ContactUpdate(ContactBase):
    """
    Schema for updating an existing contact.
    """

class ContactOut(ContactBase):
    """
    Output schema for returning contact data from the API.
    """
    id: int

    class Config:
        from_attributes = True
