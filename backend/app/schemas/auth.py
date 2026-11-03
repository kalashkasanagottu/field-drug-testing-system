from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    badge_number: Optional[str] = None
    role: str
    department: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = "Forensic Field Operations"
    role: Optional[str] = "FIELD_OFFICER"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    badge_number: Optional[str] = None
    department: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None  # Returned in demo/dev mode only
    expires_in: int


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
