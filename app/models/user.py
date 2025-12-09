"""
SQLAlchemy model for storing user information.
"""

from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class User(Base):
    """SQLAlchemy model for storing user information.

    Attributes
    ----------
    id : int
        Primary key.
    username : str
        Unique username.
    email : str
        Unique email address.
    hashed_password : str
        Bcrypt-hashed password.
    is_active : bool
        Whether the user is active.
    is_verified : bool
        Whether the user has verified their email.
    avatar_url : str | None
        Optional link to the user's avatar.
    role : str
        User role (e.g., "user", "admin").
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    role = Column(String, default="user")
