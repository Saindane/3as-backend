from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    hash_password,
    create_token_pair,
    create_access_token,
    decode_token,
)
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    OTPSendRequest,
    OTPVerifyRequest,
    OTPVerifyResponse,
    PasswordResetRequest,
)
from app.utils.otp import generate_otp, save_otp, verify_otp, send_sms_otp


def login(db: Session, payload: LoginRequest, ip: str) -> TokenResponse:
    user = db.query(User).filter(User.mobile == payload.mobile).first()

    if not user or not verify_password(payload.password, user.password_hash):
        _log(db, None, "LOGIN_FAILED", detail=f"mobile={payload.mobile}", ip=ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact admin.",
        )

    tokens = create_token_pair(user.user_id, user.role.value)
    _log(db, user.user_id, "LOGIN_SUCCESS", entity="User", entity_id=user.user_id, ip=ip)

    return TokenResponse(
        **tokens,
        user_id=user.user_id,
        name=user.name,
        role=user.role.value,
    )


def refresh_tokens(db: Session, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    tokens = create_token_pair(user.user_id, user.role.value)
    return TokenResponse(**tokens, user_id=user.user_id, name=user.name, role=user.role.value)


def send_otp(db: Session, payload: OTPSendRequest) -> dict:
    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this mobile number",
        )

    otp = generate_otp(4)
    save_otp(db, payload.mobile, otp, payload.purpose)
    send_sms_otp(payload.mobile, otp)

    return {"message": f"OTP sent to +91{payload.mobile[-4:].rjust(10, '*')}"}


def verify_otp_and_get_token(db: Session, payload: OTPVerifyRequest) -> OTPVerifyResponse:
    is_valid = verify_otp(db, payload.mobile, payload.otp, payload.purpose)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # Issue a short-lived reset token (5 minutes)
    reset_token = create_access_token(
        data={"sub": payload.mobile, "purpose": payload.purpose},
        expires_delta=timedelta(minutes=5),
    )

    return OTPVerifyResponse(verified=True, reset_token=reset_token)


def reset_password(db: Session, payload: PasswordResetRequest) -> dict:
    token_payload = decode_token(payload.reset_token)
    if (
        not token_payload
        or token_payload.get("sub") != payload.mobile
        or token_payload.get("purpose") != "password_reset"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    _log(db, user.user_id, "PASSWORD_RESET", entity="User", entity_id=user.user_id)

    return {"message": "Password updated successfully"}


def update_fcm_token(db: Session, user: User, fcm_token: str) -> dict:
    user.fcm_token = fcm_token
    db.commit()
    return {"message": "FCM token updated"}


# ── Private helpers ────────────────────────────────────────────────

def _log(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity: str = None,
    entity_id: int = None,
    detail: str = None,
    ip: str = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip,
    )
    db.add(log)
    db.commit()
