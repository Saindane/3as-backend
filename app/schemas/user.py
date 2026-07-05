from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    name:     str
    mobile:   str
    email:    Optional[str] = None
    password: str
    role:     str = "resident"

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not re.fullmatch(r"[6-9]\d{9}", v):
            raise ValueError("Enter a valid 10-digit mobile number")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        
        if v.lower() not in ("resident", "management", "admin"):
            raise ValueError("Role must be resident, management, or admin")
        return v.lower()


class UserUpdate(BaseModel):
    name:      Optional[str]  = None
    email:     Optional[str]  = None
    role:      Optional[str]  = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    user_id:    int
    name:       str
    mobile:     str
    email:      Optional[str]
    role:       str
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
