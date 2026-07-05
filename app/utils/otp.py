import random
import string
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.otp import OTPRecord


def generate_otp(length: int = 4) -> str:
    """Generate a numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def _hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def _verify_otp_hash(otp: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(otp.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def save_otp(db: Session, mobile: str, otp: str, purpose: str) -> OTPRecord:
    """Hash and save OTP. Invalidate any existing OTPs for same mobile+purpose."""
    db.query(OTPRecord).filter(
        OTPRecord.mobile  == mobile,
        OTPRecord.purpose == purpose,
        OTPRecord.is_used == False,
    ).update({"is_used": True})

    record = OTPRecord(
        mobile=mobile,
        otp_hash=_hash_otp(otp),
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
            OTPRecord.mobile    == mobile,
            OTPRecord.purpose   == purpose,
            OTPRecord.is_used   == False,
            OTPRecord.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPRecord.created_at.desc())
        .first()
    )

    if not record:
        return False

    if not _verify_otp_hash(otp, record.otp_hash):
        return False

    record.is_used = True
    db.commit()
    return True


def send_sms_otp(mobile: str, otp: str) -> bool:
    """Send OTP via SMS. In dev mode, prints to console."""
    print(f"[OTP] +91{mobile} → {otp}  (dev mode — SMS not sent)")
    return True
