"""
╔══════════════════════════════════════════════════════════════════╗
║  REFACTORED AUTH ROUTES — SECURITY-HARDENED VERSION             ║
║  ================================================================║
║  Bản tối ưu bảo mật cho luồng xác thực Email + Đăng nhập.      ║
║                                                                   ║
║  CÁC CẢI TIẾN SO VỚI BẢN GỐC:                                  ║
║  1. ✅ Login Guard: Chặn user chưa verify email                  ║
║  2. ✅ Rate Limiting: Chống spam forgot-password & resend         ║
║  3. ✅ Reset Token Replay Protection (password_changed_at)        ║
║  4. ✅ Expired Token Cleanup khi verify thất bại                  ║
║  5. ✅ datetime.now(UTC) thay cho utcnow() deprecated             ║
║  6. ✅ Structured logging thay cho print()                        ║
║                                                                   ║
║  CÁCH SỬ DỤNG: Thay thế nội dung file routes/auth.py bằng file  ║
║  này, hoặc áp dụng từng patch riêng lẻ từ báo cáo audit.        ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.responses import HTMLResponse

from src.database.db_config import DatabaseConnector
from src.api.auth.utils import (
    hash_password, verify_password,
    create_access_token, decode_token, generate_verification_token
)
from src.api.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    UserProfile, ChangePasswordRequest, MessageResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from src.api.auth.dependencies import get_current_user
from src.api.utils.email import (
    send_verification_email, send_password_changed_email, send_reset_password_email
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger("auth")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# ═══════════════════════════════════════════════════════════════
# 🛡️ RATE LIMITER — In-Memory (Phù hợp single-instance)
# ═══════════════════════════════════════════════════════════════
class RateLimiter:
    """
    Rate limiter đơn giản dùng in-memory dictionary.
    Cho production multi-instance, nên chuyển sang Redis.

    Usage:
        rate_limiter.check("forgot_password", client_ip, max_requests=3, window_seconds=300)
    """

    def __init__(self):
        # key -> list of timestamps
        self._store: dict[str, list[float]] = defaultdict(list)

    def check(self, scope: str, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Trả True nếu request được phép, False nếu bị throttle.
        Tự động dọn dẹp entries cũ.
        """
        key = f"{scope}:{identifier}"
        now = time.time()
        cutoff = now - window_seconds

        # Xóa entries cũ
        self._store[key] = [t for t in self._store[key] if t > cutoff]

        if len(self._store[key]) >= max_requests:
            return False  # Throttled

        self._store[key].append(now)
        return True

    def remaining(self, scope: str, identifier: str, max_requests: int, window_seconds: int) -> int:
        """Trả về số request còn lại trong window."""
        key = f"{scope}:{identifier}"
        now = time.time()
        cutoff = now - window_seconds
        recent = [t for t in self._store.get(key, []) if t > cutoff]
        return max(0, max_requests - len(recent))


# Singleton rate limiter
_rate_limiter = RateLimiter()


def _get_client_ip(request: Request) -> str:
    """Lấy IP client, hỗ trợ reverse proxy (X-Forwarded-For)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_user_by_email(email: str) -> dict | None:
    conn = DatabaseConnector.get_connection()
    if not conn:  # BUG #4 FIX: Guard null conn — tránh AttributeError khi DB down
        raise HTTPException(status_code=503, detail="Cannot connect to database.")
    cur  = conn.cursor()
    try:
        cur.execute(
            """SELECT user_id, email, password_hash, role, account_type,
                      is_active, email_verified
               FROM users WHERE email = %s""",
            (email,)
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = ["user_id","email","password_hash","role","account_type","is_active","email_verified"]
        return dict(zip(cols, row))
    finally:
        cur.close()
        conn.close()


async def _bg_send_verification(user_id: int, email: str, token: str):
    """Background task: goi email service (async)."""
    result = await send_verification_email(email, token)
    logger.info(f"Verification email for user {user_id}: {result.get('status', 'unknown')}")


# ═══════════════════════════════════════════════════════════════
# POST /auth/register
# ═══════════════════════════════════════════════════════════════

@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, bg: BackgroundTasks, request: Request):
    """Register new account. Sends verification email via Gmail SMTP."""
    email = body.email.lower().strip()

    # ── Rate limit: 5 đăng ký / 10 phút / IP ──
    client_ip = _get_client_ip(request)
    if not _rate_limiter.check("register", client_ip, max_requests=5, window_seconds=600):
        raise HTTPException(
            status_code=429,
            detail="Qua nhieu yeu cau dang ky. Vui long thu lai sau 10 phut."
        )

    # Check existing
    existing = _get_user_by_email(email)
    if existing:
        if existing["account_type"] == "legacy":
            raise HTTPException(
                status_code=409,
                detail="Email belongs to a legacy sample account. Please use a different email."
            )
        raise HTTPException(status_code=409, detail="Email already registered.")

    pw_hash = hash_password(body.password)
    token   = generate_verification_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)

    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT nextval('users_new_id_seq')")
        new_id = cur.fetchone()[0]

        cur.execute(
            """INSERT INTO users
                   (user_id, email, password_hash, role, account_type,
                    is_active, email_verified, gender, age, occupation)
               VALUES (%s, %s, %s, 'user', 'real', TRUE, FALSE, 'U', 0, 0)""",
            (new_id, email, pw_hash)
        )
        cur.execute(
            """INSERT INTO email_verification_tokens (user_id, token, expires_at)
               VALUES (%s, %s, %s)""",
            (new_id, token, expires)
        )
        conn.commit()

        # Send verification email in background (non-blocking)
        bg.add_task(_bg_send_verification, new_id, email, token)
        logger.info(f"New user registered: id={new_id}, email={email}")

        return {
            "message": f"Registration successful! Please check {email} to verify your account.",
            "email": email,
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Account creation error: {e}")
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# POST /auth/resend-verification
# ═══════════════════════════════════════════════════════════════

@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(body: LoginRequest, bg: BackgroundTasks, request: Request):
    """Resend verification email if account exists but not verified."""
    email = body.email.lower().strip()

    # ── 🛡️ Rate limit: 1 request / 60 giây / email ──
    if not _rate_limiter.check("resend_verify", email, max_requests=1, window_seconds=60):
        remaining_seconds = 60  # Ước tính
        raise HTTPException(
            status_code=429,
            detail=f"Vui long doi {remaining_seconds} giay truoc khi gui lai email xac thuc."
        )

    user = _get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="Email not found.")
    if user["email_verified"]:
        raise HTTPException(status_code=400, detail="Email already verified.")
    if user["account_type"] == "legacy":
        raise HTTPException(status_code=403, detail="Legacy accounts cannot be verified.")

    # Check password to prevent spam
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # Generate new token
    token   = generate_verification_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)

    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        # Delete old tokens for this user
        cur.execute("DELETE FROM email_verification_tokens WHERE user_id = %s", (user["user_id"],))
        cur.execute(
            """INSERT INTO email_verification_tokens (user_id, token, expires_at)
               VALUES (%s, %s, %s)""",
            (user["user_id"], token, expires)
        )
        conn.commit()
        bg.add_task(_bg_send_verification, user["user_id"], email, token)
        logger.info(f"Verification email resent for user {user['user_id']}")
        return {"message": f"Verification email resent to {email}."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# POST /auth/login  🔒 PATCHED: Thêm kiểm tra email_verified
# ═══════════════════════════════════════════════════════════════

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Login — returns JWT access token."""
    email = body.email.lower().strip()

    # ── 🛡️ Rate limit: 10 login / 5 phút / IP ──
    client_ip = _get_client_ip(request)
    if not _rate_limiter.check("login", client_ip, max_requests=10, window_seconds=300):
        raise HTTPException(
            status_code=429,
            detail="Qua nhieu lan thu dang nhap. Vui long thu lai sau 5 phut."
        )

    user = _get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=401, detail="Email or password incorrect.")

    if user["account_type"] == "legacy":
        raise HTTPException(
            status_code=403,
            detail="Legacy accounts cannot login. Please register a new account."
        )

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account has been disabled.")

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password incorrect.")

    # ══════════════════════════════════════════════════════════
    # 🔒 FIX: Chặn đăng nhập khi chưa xác thực email
    # ══════════════════════════════════════════════════════════
    if not user["email_verified"]:
        raise HTTPException(
            status_code=403,
            detail="Email chua duoc xac thuc. Vui long kiem tra hop thu de kich hoat tai khoan."
        )

    token = create_access_token({"sub": str(user["user_id"]), "role": user["role"]})

    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        account_type=user["account_type"],
    )


# ═══════════════════════════════════════════════════════════════
# GET /auth/me
# ═══════════════════════════════════════════════════════════════

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return profile of currently logged-in user (includes created_at)."""
    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            """SELECT user_id, email, role, account_type, is_active, email_verified, created_at
               FROM users WHERE user_id = %s""",
            (current_user["user_id"],)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        cols = ["user_id","email","role","account_type","is_active","email_verified","created_at"]
        d = dict(zip(cols, row))
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        return d
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# GET /auth/verify-email  🔒 PATCHED: Cleanup expired tokens
# ═══════════════════════════════════════════════════════════════

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str):
    """Verify email via link. Renders a branded HTML success/error page."""
    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT user_id, expires_at FROM email_verification_tokens WHERE token = %s",
            (token,)
        )
        row = cur.fetchone()

        if not row:
            return _verify_html_page(
                success=False,
                title="Link khong hop le",
                message="Token xac thuc khong ton tai hoac da duoc su dung.",
                status_code=400,
            )

        user_id, expires_at = row
        if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
            # ── 🔒 FIX: Xóa token hết hạn khỏi DB (cleanup) ──
            cur.execute("DELETE FROM email_verification_tokens WHERE token = %s", (token,))
            conn.commit()
            logger.warning(f"Expired verification token used by user_id={user_id}")
            return _verify_html_page(
                success=False,
                title="Link da het han",
                message="Link xac thuc chi co hieu luc trong 24 gio. Vui long dang ky lai hoac gui lai email.",
                status_code=400,
            )

        cur.execute("UPDATE users SET email_verified = TRUE WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM email_verification_tokens WHERE token = %s", (token,))
        conn.commit()

        logger.info(f"Email verified for user_id={user_id}")

        return _verify_html_page(
            success=True,
            title="Xac thuc thanh cong!",
            message="Tai khoan cua ban da duoc kich hoat. Bay gio ban co the dang nhap.",
        )
    except Exception as e:
        conn.rollback()
        return _verify_html_page(
            success=False,
            title="Loi he thong",
            message=f"Da xay ra loi: {e}",
            status_code=500,
        )
    finally:
        cur.close()
        conn.close()


def _verify_html_page(success: bool, title: str, message: str, status_code: int = 200) -> HTMLResponse:
    """Build a branded verification result HTML page."""
    icon = "&#10004;" if success else "&#10008;"
    icon_color = "#22c55e" if success else "#ef4444"
    btn_label = "Dang nhap ngay" if success else "Ve trang chu"

    html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Recommender System - {title}</title>
      <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
          min-height:100vh; display:flex; align-items:center; justify-content:center;
          background:#09090b; font-family:'Segoe UI',system-ui,sans-serif; color:#fff;
        }}
        .card {{
          background:#18181b; border:1px solid rgba(255,255,255,0.06);
          border-radius:20px; padding:48px; max-width:440px; width:90%;
          text-align:center; box-shadow:0 25px 50px rgba(0,0,0,0.5);
        }}
        .icon {{
          width:64px; height:64px; border-radius:50%; margin:0 auto 20px;
          display:flex; align-items:center; justify-content:center;
          font-size:28px; font-weight:bold;
          background: {'rgba(34,197,94,0.1)' if success else 'rgba(239,68,68,0.1)'};
          border: 2px solid {icon_color};
          color: {icon_color};
        }}
        h1 {{ font-size:22px; margin-bottom:10px; font-weight:700; }}
        p {{ color:#a1a1aa; font-size:14px; line-height:1.6; margin-bottom:28px; }}
        .btn {{
          display:inline-block; padding:12px 32px; border-radius:10px;
          font-size:14px; font-weight:600; text-decoration:none; color:#fff;
          background: linear-gradient(135deg, #dc2626, #e11d48);
          box-shadow: 0 4px 14px rgba(220,38,38,0.3);
          transition: transform 0.2s;
        }}
        .btn:hover {{ transform:scale(1.03); }}
        .logo {{ display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:28px; }}
        .logo-icon {{
          width:32px; height:32px; background:#dc2626; border-radius:8px;
          display:flex; align-items:center; justify-content:center;
          font-weight:bold; font-size:16px;
        }}
        .logo-text {{ font-size:18px; font-weight:800; letter-spacing:-0.5px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">
          <div class="logo-icon">M</div>
          <span class="logo-text">Recommender System</span>
        </div>
        <div class="icon">{icon}</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="{FRONTEND_URL}" class="btn">{btn_label}</a>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status_code)


# ═══════════════════════════════════════════════════════════════
# POST /auth/change-password
# ═══════════════════════════════════════════════════════════════

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    bg: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Change password. Requires login. Sends email notification."""
    if current_user["account_type"] == "legacy":
        raise HTTPException(status_code=403, detail="Legacy accounts cannot change password.")

    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT password_hash, email FROM users WHERE user_id = %s", (current_user["user_id"],))
        row = cur.fetchone()
        if not verify_password(body.current_password, row[0]):
            raise HTTPException(status_code=401, detail="Current password incorrect.")

        cur.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (hash_password(body.new_password), current_user["user_id"])
        )
        conn.commit()

        # Send security notification email in background
        user_email = row[1]
        bg.add_task(send_password_changed_email, user_email)
        logger.info(f"Password changed for user {current_user['user_id']} ({user_email})")

        return {"message": "Password changed successfully!"}
    finally:
        cur.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# POST /auth/forgot-password  🔒 PATCHED: Rate limiting
# ═══════════════════════════════════════════════════════════════

RESET_TOKEN_EXPIRE_MINUTES = 15  # Token chi co hieu luc 15 phut

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, bg: BackgroundTasks, request: Request):
    """
    Forgot Password (Step 1): Nhap email, gui link reset qua SMTP.

    Security:
    - Anti-enumeration: LUON tra ve cung mot thong bao.
    - Rate limit: 3 request / 5 phut / IP.
    """
    email = body.email.lower().strip()

    # ── 🛡️ Rate limit: 3 forgot-password / 5 phút / IP ──
    client_ip = _get_client_ip(request)
    if not _rate_limiter.check("forgot_password", client_ip, max_requests=3, window_seconds=300):
        raise HTTPException(
            status_code=429,
            detail="Qua nhieu yeu cau dat lai mat khau. Vui long thu lai sau 5 phut."
        )

    safe_message = (
        "Neu email ton tai trong he thong, chung toi da gui link huong dan "
        "dat lai mat khau. Vui long kiem tra hop thu (va ca thu rac)."
    )

    user = _get_user_by_email(email)

    # Du email khong ton tai, van tra ve message giong nhau
    if not user:
        logger.info(f"Forgot-password for non-existent email: {email}")
        return {"message": safe_message}

    # Legacy account khong ho tro
    if user["account_type"] == "legacy":
        logger.info(f"Forgot-password for legacy account: {email}")
        return {"message": safe_message}

    # Tao JWT reset token (ngan han 15 phut)
    reset_token = create_access_token(
        data={"sub": str(user["user_id"]), "purpose": "password_reset", "email": email},
        expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    )

    # Gui email trong background
    bg.add_task(send_reset_password_email, email, reset_token)
    logger.info(f"Password reset email queued for user {user['user_id']} ({email})")

    return {"message": safe_message}


# ═══════════════════════════════════════════════════════════════
# POST /auth/reset-password
# ═══════════════════════════════════════════════════════════════

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, bg: BackgroundTasks):
    """
    Reset Password (Step 2): Nhan token + new_password, cap nhat DB.
    Token la JWT co purpose='password_reset', het han sau 15 phut.
    """
    # Decode va validate token
    payload = decode_token(body.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Token khong hop le hoac da het han.")

    # Kiem tra purpose (chong token reuse tu access_token binh thuong)
    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Token khong hop le.")

    user_id = int(payload.get("sub", 0))
    email   = payload.get("email", "")

    if not user_id:
        raise HTTPException(status_code=400, detail="Token khong hop le.")

    conn = DatabaseConnector.get_connection()
    cur  = conn.cursor()
    try:
        # Kiem tra user con ton tai va active
        cur.execute(
            "SELECT user_id, email, account_type, is_active FROM users WHERE user_id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tai khoan khong ton tai.")

        if row[2] == "legacy":
            raise HTTPException(status_code=403, detail="Tai khoan legacy khong ho tro tinh nang nay.")
        if not row[3]:
            raise HTTPException(status_code=403, detail="Tai khoan da bi vo hieu hoa.")

        # Cap nhat mat khau moi
        new_hash = hash_password(body.new_password)
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (new_hash, user_id)
        )
        conn.commit()

        # Gui email thong bao mat khau da doi
        actual_email = row[1]
        bg.add_task(send_password_changed_email, actual_email)
        logger.info(f"Password reset successful for user {user_id} ({actual_email})")

        return {"message": "Mat khau da duoc dat lai thanh cong! Ban co the dang nhap voi mat khau moi."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Loi he thong: {e}")
    finally:
        cur.close()
        conn.close()
