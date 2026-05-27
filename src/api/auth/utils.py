"""
Auth Utilities: JWT + Password Hashing
Dùng bcrypt trực tiếp (không qua passlib) để tránh lỗi tương thích.
"""
import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-dev-secret-change-in-prod")
ALGORITHM  = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))


# ── Password ───────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """Hash mật khẩu bằng bcrypt (trực tiếp, không qua passlib)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """So sánh mật khẩu. Trả False ngay nếu là legacy account."""
    if hashed == "LEGACY_ACCOUNT_NO_LOGIN":
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT ────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.utcnow() + (expires_delta or timedelta(minutes=EXPIRE_MIN))
    payload.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── Email Verification Token ───────────────────────────────
def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)
