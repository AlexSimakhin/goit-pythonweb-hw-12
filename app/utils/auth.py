"""
Utility functions for password hashing, JWT token creation, email verification, refresh/access/reset tokens.
"""
import os
import smtplib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from email.mime.text import MIMEText

from passlib.context import CryptContext
from jose import jwt, JWTError
from email_validator import validate_email, EmailNotValidError

SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY', SECRET_KEY)
REFRESH_TOKEN_EXPIRE_DAYS = 7
RESET_SECRET_KEY = os.getenv('RESET_SECRET_KEY', SECRET_KEY)
RESET_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Returns
    -------
    bool
        True if the password matches the hash, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Parameters
    ----------
    password : str
        Plain text password to hash.

    Returns
    -------
    str
        Bcrypt hash string.
    """
    return pwd_context.hash(password)


def _encode(data: Dict[str, Any], key: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key, algorithm=ALGORITHM)


def _decode(token: str, key: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    return _encode(data, SECRET_KEY, expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT access token or return None if invalid."""
    return _decode(token, SECRET_KEY)


# -- Redis-backed current user helper --
try:
    # Import lazily to avoid hard dependency during certain test runs
    from app.utils.cache import get_cached_user as _get_cached_user  # type: ignore
except ImportError:
    def _get_cached_user(_user_id: int):  # type: ignore
        """Stubbed cache getter when Redis is unavailable."""
        return None


def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    """Return current user data from Redis cache using the JWT access token.

    This avoids hitting the database on every request. If token is invalid or
    cache miss occurs, returns None. Ensure login flow caches user data.
    """
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if user_id is None:
        return None
    cached = _get_cached_user(int(user_id))
    # Optional safety check: ensure cached email matches token
    if cached and cached.get("email") == payload.get("email"):
        return cached
    return None


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token."""
    return _encode(data, REFRESH_SECRET_KEY, expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT refresh token or return None if invalid."""
    return _decode(token, REFRESH_SECRET_KEY)


def create_reset_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed reset token embedding the user_id for password reset flows."""
    return _encode({"user_id": user_id}, RESET_SECRET_KEY, expires_delta or timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES))


def verify_reset_token(token: str) -> Optional[int]:
    """Verify and decode a reset token, returning user_id if valid."""
    payload = _decode(token, RESET_SECRET_KEY)
    if not payload:
        return None
    return payload.get("user_id")


def _smtp_send(to_email: str, subject: str, body: str) -> bool:
    """Internal helper to send an email using environment-configured SMTP.

    Respects SMTP_HOST, SMTP_PORT, SMTP_TLS, SMTP_USER and either SMTP_PASSWORD or SMTP_PASS, and SMTP_FROM.
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to_email
    msg["From"] = os.getenv("SMTP_FROM", "noreply@example.com")

    host = os.getenv("SMTP_HOST", "localhost")
    port = int(os.getenv("SMTP_PORT", "1025"))
    try:
        with smtplib.SMTP(host, port) as server:
            if os.getenv("SMTP_TLS", "0") == "1":
                server.starttls()
            user = os.getenv("SMTP_USER")
            # Support both SMTP_PASSWORD and SMTP_PASS variable names
            pwd = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS")
            if user and pwd:
                server.login(user, pwd)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError):
        return False


def send_verification_email(to_email: str, user_id: int) -> bool:
    """Send a simple verification email containing a link with the user_id. Returns True on success.

    This function validates the email, builds a message and attempts to send via SMTP.
    It is intentionally simple to allow unit tests to mock smtplib.SMTP.
    """
    # Validate email syntax only (no DNS lookups)
    try:
        validate_email(to_email, check_deliverability=False)
    except EmailNotValidError:
        return False

    subject = "Verify your email"
    body = f"Please verify your account by visiting /users/verify/{user_id}"
    return _smtp_send(to_email, subject, body)


def send_reset_email(to_email: str, reset_token: str) -> bool:
    """Send a password reset email with a tokenized link.

    The link path can be configured via RESET_URL_BASE or defaults to /users/reset-password.
    """
    try:
        validate_email(to_email, check_deliverability=False)
    except EmailNotValidError:
        return False

    base = os.getenv("RESET_URL_BASE", "")
    link = f"{base}/users/reset-password?token={reset_token}" if base else f"/users/reset-password?token={reset_token}"
    subject = "Password reset instructions"
    body = (
        "You requested a password reset. If this wasn't you, ignore this email.\n\n"
        f"Use the following link to reset your password (valid for {RESET_TOKEN_EXPIRE_MINUTES} minutes):\n{link}\n\n"
        "Alternatively, copy this token and use it in the API: \n" + reset_token
    )
    return _smtp_send(to_email, subject, body)
