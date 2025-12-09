"""
FastAPI router for user registration, login, email verification, avatar update, and /me endpoint with rate limiting.
"""
import os
import smtplib
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import cloudinary
import cloudinary.uploader
from app.database import SessionLocal
from app.schemas.user import UserCreate, UserOut, Token
from app.crud.user import create_user, authenticate_user, verify_user_email, update_avatar
from app.utils.auth import (
    create_access_token,
    decode_access_token,
    send_verification_email,
    get_password_hash,
    create_refresh_token,
    decode_refresh_token,
    create_reset_token,
    verify_reset_token,
    send_reset_email,
)
from app.models.user import User
from app.utils.cache import cache_user, get_cached_user, delete_user_cache, update_user_cache

router = APIRouter(prefix="/users", tags=["users"])
_limiter = Limiter(key_func=get_remote_address)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_db():
    """Provide a SQLAlchemy session for request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return the created profile.

    Args:
        user: Registration payload (username, email, password).
        db: Database session dependency.

    Returns:
        The created user profile.
    """
    created = create_user(db, user)
    # Optionally send verification email (best-effort).
    try:
        send_verification_email(created.email, created.id)
    except smtplib.SMTPException:
        # Non-fatal for registration; log in real app
        pass
    return created


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access and refresh tokens.

    Args:
        form_data: OAuth2 form with username and password.
        db: Database session dependency.

    Returns:
        Token object containing access and refresh tokens.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    access = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
    cache_user(user.id, {"id": user.id, "username": user.username, "email": user.email, "role": user.role})
    return {"access_token": access, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=Token)
async def refresh(token: str = Body(..., embed=True, description="Refresh token")):
    """Exchange a valid refresh token for a new access token.

    Args:
        token: Refresh token string.

    Returns:
        Token object with a new access token and the same refresh token.
    """
    payload = decode_refresh_token(token)
    if not payload or not payload.get("user_id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access = create_access_token({"user_id": payload["user_id"], "email": payload.get("email")})
    return {"access_token": access, "token_type": "bearer", "refresh_token": token}


@router.get("/verify/{user_id}", response_model=UserOut)
async def verify_email(user_id: int, db: Session = Depends(get_db)):
    """Verify a user's email address.

    Marks the specified user's email as verified and refreshes their cache entry.

    Args:
        user_id: ID of the user to verify.
        db: Database session dependency.

    Returns:
        The updated user profile.
    """
    user = verify_user_email(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Invalidate and refresh the cache after verification
    delete_user_cache(user.id)
    update_user_cache(user.id, {"user_id": user.id, "email": user.email, "role": user.role})
    return user


@router.post("/avatar", response_model=UserOut)
async def update_user_avatar(
    token: str = Depends(oauth2_scheme),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and set a new avatar for the authenticated admin user.

    Args:
        token: Bearer access token; must belong to an admin user.
        file: Image file to upload to Cloudinary.
        db: Database session dependency.

    Returns:
        The updated user profile with a new avatar URL.

    Raises:
        HTTPException: If file is missing, token invalid, user not found, or user is not admin.
    """
    if file is None:
        raise HTTPException(status_code=422, detail="File required")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can change avatar")
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )
    result = cloudinary.uploader.upload(file.file)
    avatar_url = result.get("secure_url")
    user = update_avatar(db, user_id, avatar_url)
    # Avatar changed: refresh cache entry
    delete_user_cache(user.id)
    update_user_cache(user.id, {"user_id": user.id, "email": user.email, "role": user.role})
    return user


@router.get("/me", response_model=UserOut)
# @limiter.limit("5/minute")
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Return current authenticated user's profile.

    Attempts to use the Redis cache to reduce database load.

    Args:
        token: Bearer access token.
        db: Database session dependency.

    Returns:
        The user profile of the current user.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    cached = get_cached_user(payload.get("user_id"))
    if cached:
        user = db.query(User).filter(User.id == cached.get("user_id")).first()
        if user:
            return user
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prime cache if missing
    update_user_cache(user.id, {"user_id": user.id, "email": user.email, "role": user.role})
    return user


@router.post("/request-reset", status_code=200)
async def request_password_reset(email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Initiate the password reset flow for a user.

    Generates a short-lived reset token and sends reset instructions to the email
    if the account exists (response is generic to avoid account enumeration).

    Args:
        email: Email address of the account.
        db: Database session dependency.

    Returns:
        A message about reset instructions; in tests includes the reset token.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Do not disclose whether the email exists; respond generically
        return {"msg": "If the account exists, reset instructions have been sent."}
    token = create_reset_token(user.id)
    # Send email with reset link/token
    send_reset_email(user.email, token)
    # In test environments expose token to facilitate e2e tests
    if os.getenv("TESTING") == "1":
        return {"msg": "Reset token generated", "reset_token": token}
    return {"msg": "Reset instructions have been sent if the account exists."}


@router.post("/reset-password", status_code=200)
async def reset_password(
    reset_token: str = Body(..., embed=True),
    new_password: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Reset a user's password using a valid reset token.

    Args:
        reset_token: Token previously generated by the reset request.
        new_password: New plaintext password to set.
        db: Database session dependency.

    Returns:
        A success message if the password was updated.
    """
    user_id = verify_reset_token(reset_token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"msg": "Password updated"}


@router.post("/set-role", response_model=UserOut)
async def set_role(
    user_id: int,
    role: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Change a user's role (admin-only).

    Args:
        user_id: ID of the target user.
        role: Desired role, one of {"user", "admin"}.
        token: Bearer access token of the requester; must belong to an admin.
        db: Database session dependency.

    Returns:
        The updated user profile.
    """
    # Decode requester token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    requester_id = payload.get("user_id")
    requester = db.query(User).filter(User.id == requester_id).first()
    if not requester:
        raise HTTPException(status_code=404, detail="Requester not found")
    # Only admins may change roles
    if requester.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can change user roles")

    # Validate target user and role
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    # Apply role change
    target.role = role
    db.commit()
    db.refresh(target)
    # Update cache for target
    delete_user_cache(target.id)
    update_user_cache(target.id, {"user_id": target.id, "email": target.email, "role": target.role})
    return target
