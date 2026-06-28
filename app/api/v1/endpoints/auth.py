from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    OTPSendRequest,
    OTPVerifyRequest,
    OTPVerifyResponse,
    PasswordResetRequest,
    MessageResponse,
    FCMTokenUpdate,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Login with mobile + password")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    return auth_service.login(db, payload, ip)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.post("/otp/send", response_model=MessageResponse, summary="Send OTP to mobile")
def send_otp(payload: OTPSendRequest, db: Session = Depends(get_db)):
    result = auth_service.send_otp(db, payload)
    return MessageResponse(message=result["message"])


@router.post("/otp/verify", response_model=OTPVerifyResponse, summary="Verify OTP")
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    return auth_service.verify_otp_and_get_token(db, payload)


@router.post("/password/reset", response_model=MessageResponse, summary="Reset password after OTP")
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    result = auth_service.reset_password(db, payload)
    return MessageResponse(message=result["message"])


@router.post("/fcm-token", response_model=MessageResponse, summary="Update FCM device token")
def update_fcm_token(
    payload: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = auth_service.update_fcm_token(db, current_user, payload.fcm_token)
    return MessageResponse(message=result["message"])


@router.get("/me", summary="Get current user info")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "mobile": current_user.mobile,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
    }
