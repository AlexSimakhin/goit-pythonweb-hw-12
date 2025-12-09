"""
Pydantic schemas for user registration, login, and output.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @staticmethod
    def password_length(v: str) -> str:
        """Validate that the password is no longer than 72 bytes (bcrypt limit)."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 bytes or fewer.")
        return v

class UserLogin(BaseModel):
    """Schema for user login: only username and password required."""
    username: str
    password: str

class UserOut(BaseModel):
    """Schema for user output information."""
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    role: str = "user"
    model_config = {"from_attributes": True}

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str
    refresh_token: str | None = None

class TokenData(BaseModel):
    """Schema for token data payload."""
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None
