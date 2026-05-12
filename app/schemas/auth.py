from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)


class EmailConfirmationRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailVerificationRequiredResponse(BaseModel):
    email_verification_required: bool = True
    message: str


class MessageResponse(BaseModel):
    message: str


class CurrentUserResponse(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    email_verified: bool
