"""
SQLAlchemy models for the Contacts REST API.
Defines the Contact model representing a contact entity in the database.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String

from app.database import Base


class Contact(Base):
    """SQLAlchemy model for storing contact information.

    Attributes
    ----------
    id : int
        Primary key.
    first_name : str
        Contact's first name.
    last_name : str
        Contact's last name.
    email : str
        Unique email address of the contact.
    phone : str
        Phone number.
    birthday : date
        Birthday date.
    extra : str | None
        Optional extra notes.
    user_id : int
        Foreign key referencing the owner user.
    """

    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    extra = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
