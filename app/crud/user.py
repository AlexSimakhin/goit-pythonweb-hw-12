"""
CRUD operations for user registration, authentication, email verification, and avatar update.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.auth import get_password_hash, verify_password


def create_user(db: Session, user: UserCreate):
    """Register a new user.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    user : UserCreate
        Validated input data.

    Returns
    -------
    User
        The newly created user.

    Raises
    ------
    HTTPException
        409 if the email or username already exists.
    """
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user by username and password.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    username : str
        Username.
    password : str
        Plaintext password.

    Returns
    -------
    User | None
        The authenticated user or None if credentials are invalid.

    Raises
    ------
    HTTPException
        401 for invalid credentials.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def verify_user_email(db: Session, user_id: int):
    """Mark user email as verified.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    user_id : int
        User id to verify.

    Returns
    -------
    User
        The updated user instance.

    Raises
    ------
    HTTPException
        404 if user not found.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user


def update_avatar(db: Session, user_id: int, avatar_url: str):
    """Update user's avatar URL and return the updated user.

    Parameters
    ----------
    db : Session
        SQLAlchemy session.
    user_id : int
        Target user id.
    avatar_url : str
        New avatar URL.

    Returns
    -------
    User
        Updated user.

    Raises
    ------
    HTTPException
        404 if user not found.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user
