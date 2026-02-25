"""
Auth Schemas

Pydantic models สำหรับ authentication
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    """Response schema สำหรับ JWT token"""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Request schema สำหรับ login"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Request schema สำหรับ register"""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=4, max_length=255)
    name: str | None = None
    email: EmailStr | None = None
    tel: str | None = None


class RegisterResponse(BaseModel):
    """Response schema สำหรับ register"""
    user_id: int
    username: str
    user_role: str
    name: str | None = None
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)