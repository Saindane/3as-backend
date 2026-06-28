import random
import string
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.otp import OTPRecord

otp_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_otp(length: int = 4) -> str:
    """Generate a numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def save_otp(db: Session, mobile: str, otp: str, purpose: str) -> OTPRecord:
    """Hash and save OTP. Invalidate any existing OTPs for same mobile+purpose."""
    # Expire old OTPs
    db.query(OTPRecord).filter(
        OTPRecord.mobile == mobile,
        OTPRecord.purpose == purpose,
        OTPRecord.is_used == False,
    ).update({"is_used": True})

    record = OTPRecord(
        mobile=mobile,
        otp_hash=otp_context.hash(otp),
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def verify_otp(db: Session, mobile: str, otp: str, purpose: str) -> bool:
    """Verify OTP and mark as used if valid."""
    record = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.mobile == mobile,
            OTPRecord.purpose == purpose,
            OTPRecord.is_used == False,
            OTPRecord.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPRecord.created_at.desc())
        .first()
    )

    if not record:
        return False

    if not otp_context.verify(otp, record.otp_hash):
        return False

    record.is_used = True
    db.commit()
    return True


def send_sms_otp(mobile: str, otp: str) -> bool:
    """
    Send OTP via SMS gateway.
    In development, OTP is logged to console.
    Replace with MSG91 / Twilio in production.
    """
    print(f"[OTP] Mobile: +91{mobile} | OTP: {otp} | (dev mode — not sent via SMS)")

    # Production example using MSG91:
    # import httpx
    # response = httpx.get(
    #     "https://api.msg91.com/api/v5/otp",
    #     params={
    #         "authkey": settings.SMS_API_KEY,
    #         "mobile": f"91{mobile}",
    #         "message": f"Your 3As Complex OTP is {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
    #         "sender": settings.SMS_SENDER_ID,
    #         "otp": otp,
    #     }
    # )
    # return response.status_code == 200

    return True
