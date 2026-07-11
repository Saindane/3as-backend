from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re


class UserCreate(BaseModel):
    name:     str
    mobile:   str
    email:    Optional[str] = None
    password: str
    role:     str = "RESIDENT"

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("+91", "")
        if not re.fullmatch(r"[6-9]\d{9}", v):
            raise ValueError("Enter a valid 10-digit mobile number")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v  # never modify password

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.upper()
        if v not in ("RESIDENT", "MANAGEMENT", "ADMIN"):
            raise ValueError("Role must be resident, management, or admin")
        return v  # return UPPERCASE to match DB enum


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
    items: List[UserResponse]
