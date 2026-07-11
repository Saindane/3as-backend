from pydantic import BaseModel, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    mobile: str
    password: str

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not re.fullmatch(r"[6-9]\d{9}", v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user_id:       int
    name:          str
    mobile:        str = ""
    role:          str


class RefreshRequest(BaseModel):
    refresh_token: str


class OTPSendRequest(BaseModel):
    mobile: str
    purpose: str = "password_reset"   # "password_reset" | "login"

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not re.fullmatch(r"[6-9]\d{9}", v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v


class OTPVerifyRequest(BaseModel):
    mobile: str
    otp: str
    purpose: str = "password_reset"

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4,6}", v):
            raise ValueError("OTP must be 4-6 digits")
        return v


class OTPVerifyResponse(BaseModel):
    verified: bool
    reset_token: Optional[str] = None   # short-lived token to allow password reset


class PasswordResetRequest(BaseModel):
    mobile: str
    reset_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class MessageResponse(BaseModel):
    message: str


class FCMTokenUpdate(BaseModel):
    fcm_token: str
