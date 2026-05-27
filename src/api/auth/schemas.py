"""
Pydantic Schemas cho Auth endpoints
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Tối thiểu 6 ký tự")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    email:        str
    role:         str
    account_type: str


class UserProfile(BaseModel):
    user_id:        int
    email:          str
    role:           str
    account_type:   str
    is_active:      bool
    email_verified: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str = Field(min_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, description="Mat khau moi, toi thieu 6 ky tu")


class MessageResponse(BaseModel):
    message: str
    email: Optional[str] = None
