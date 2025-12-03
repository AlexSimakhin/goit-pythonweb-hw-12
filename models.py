"""
SQLAlchemy models for the Contacts REST API.
Defines the Contact model representing a contact entity in the database.
"""

from sqlalchemy import Column, Integer, String, Date
from database import Base

class Contact(Base):
    """
    SQLAlchemy model for storing contact information.
    """
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    extra = Column(String, nullable=True)
