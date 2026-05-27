"""
Email Service — Gmail SMTP via fastapi-mail
============================================
Cau hinh qua .env:
  MAIL_USERNAME=your_email@gmail.com
  MAIL_PASSWORD=your_app_password    (Mat khau ung dung 16 ky tu)
  MAIL_FROM=your_email@gmail.com
  MAIL_SERVER=smtp.gmail.com
  MAIL_PORT=587
"""
import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

# ── SMTP Configuration ────────────────────────────────────
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM     = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_SERVER   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT     = int(os.getenv("MAIL_PORT", 587))
FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")
APP_BASE_URL  = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

# Flag: email co duoc bat hay khong
EMAIL_ENABLED = bool(MAIL_USERNAME and MAIL_PASSWORD and MAIL_PASSWORD != "your_app_password")

if EMAIL_ENABLED:
    conf = ConnectionConfig(
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_FROM=MAIL_FROM,
        MAIL_FROM_NAME="Recommender System",
        MAIL_PORT=MAIL_PORT,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    fast_mail = FastMail(conf)
    print("[EMAIL] SMTP configured OK — real emails will be sent")
else:
    fast_mail = None
    print("[EMAIL] SMTP not configured — emails will be logged to console only")


def _build_verification_html(verify_url: str, user_email: str) -> str:
    """Build HTML email template dong bo voi giao dien Recommender System."""
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0; padding:0; background-color:#09090b; font-family:'Segoe UI',Roboto,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#09090b; padding:40px 0;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0"
                 style="background-color:#18181b; border-radius:16px; overflow:hidden;
                        border:1px solid rgba(255,255,255,0.06);">

            <!-- Gradient top bar -->
            <tr><td style="height:4px; background:linear-gradient(90deg,#dc2626,#f43f5e,#f97316);"></td></tr>

            <!-- Logo -->
            <tr><td style="padding:32px 40px 0 40px;">
              <table cellpadding="0" cellspacing="0"><tr>
                <td style="width:36px; height:36px; background-color:#dc2626; border-radius:10px; text-align:center; vertical-align:middle;">
                  <span style="color:#fff; font-size:18px; font-weight:bold;">M</span>
                </td>
                <td style="padding-left:10px; color:#fff; font-size:20px; font-weight:800; letter-spacing:-0.5px;">
                  Recommender System
                </td>
              </tr></table>
            </td></tr>

            <!-- Title -->
            <tr><td style="padding:24px 40px 0 40px;">
              <h1 style="color:#ffffff; font-size:22px; margin:0 0 8px 0; font-weight:700;">
                Xac thuc tai khoan cua ban
              </h1>
              <p style="color:#a1a1aa; font-size:14px; line-height:1.6; margin:0;">
                Cam on ban da dang ky <strong style="color:#f4f4f5;">{user_email}</strong>
                tren Recommender System. Click nut ben duoi de kich hoat tai khoan va bat dau nhan goi y phim tu AI.
              </p>
            </td></tr>

            <!-- CTA Button -->
            <tr><td style="padding:28px 40px 0 40px;" align="center">
              <a href="{verify_url}"
                 style="display:inline-block; padding:14px 40px;
                        background: linear-gradient(135deg, #dc2626, #e11d48);
                        color:#ffffff; font-size:15px; font-weight:700;
                        text-decoration:none; border-radius:10px;
                        box-shadow: 0 4px 14px rgba(220,38,38,0.35);">
                Xac thuc Email
              </a>
            </td></tr>

            <!-- Fallback link -->
            <tr><td style="padding:20px 40px 0 40px;">
              <p style="color:#71717a; font-size:11px; line-height:1.5; word-break:break-all;">
                Neu nut khong hoat dong, copy link sau vao trinh duyet:<br/>
                <a href="{verify_url}" style="color:#f97316; text-decoration:none;">{verify_url}</a>
              </p>
            </td></tr>

            <!-- Divider -->
            <tr><td style="padding:24px 40px 0 40px;">
              <div style="border-top:1px solid rgba(255,255,255,0.06);"></div>
            </td></tr>

            <!-- Footer -->
            <tr><td style="padding:16px 40px 28px 40px;">
              <p style="color:#52525b; font-size:11px; margin:0; line-height:1.5;">
                Link nay se het han sau <strong>24 gio</strong>.<br/>
                Neu ban khong dang ky tai khoan nay, vui long bo qua email nay.
              </p>
              <p style="color:#3f3f46; font-size:10px; margin:12px 0 0 0;">
                &copy; 2026 Recommender System — Hybrid AI Movie Recommender System
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


async def send_verification_email(user_email: str, token: str):
    """
    Gui email xac thuc. Neu SMTP chua cau hinh thi chi log ra console.
    Duoc goi tu BackgroundTasks de khong block API response.
    """
    verify_url = f"{APP_BASE_URL}/auth/verify-email?token={token}"

    if not EMAIL_ENABLED or fast_mail is None:
        # Fallback: log to console
        print(f"\n{'='*60}")
        print(f"[EMAIL-LOG] To: {user_email}")
        print(f"[EMAIL-LOG] Verify URL: {verify_url}")
        print(f"{'='*60}\n")
        return {"status": "logged", "detail": "SMTP not configured, logged to console"}

    html_body = _build_verification_html(verify_url, user_email)

    message = MessageSchema(
        subject="[Recommender System] Xac thuc tai khoan cua ban",
        recipients=[user_email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        await fast_mail.send_message(message)
        print(f"[EMAIL] Sent verification email to {user_email}")
        return {"status": "sent"}
    except Exception as e:
        error_msg = str(e)
        print(f"[EMAIL ERROR] Failed to send to {user_email}: {error_msg}")
        # Phan tich loi SMTP cu the
        if "535" in error_msg or "Authentication" in error_msg.lower():
            print("[EMAIL HINT] Check MAIL_PASSWORD — must be 16-char App Password, not Gmail password")
            print("[EMAIL HINT] Go to https://myaccount.google.com/apppasswords to generate one")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print("[EMAIL HINT] Check MAIL_SERVER and MAIL_PORT — firewall may block port 587")
        return {"status": "error", "detail": error_msg}


def _build_password_changed_html(user_email: str) -> str:
    """Build HTML email thong bao doi mat khau thanh cong."""
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0; padding:0; background-color:#09090b; font-family:'Segoe UI',Roboto,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#09090b; padding:40px 0;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0"
                 style="background-color:#18181b; border-radius:16px; overflow:hidden;
                        border:1px solid rgba(255,255,255,0.06);">

            <!-- Gradient top bar -->
            <tr><td style="height:4px; background:linear-gradient(90deg,#dc2626,#f43f5e,#f97316);"></td></tr>

            <!-- Logo -->
            <tr><td style="padding:32px 40px 0 40px;">
              <table cellpadding="0" cellspacing="0"><tr>
                <td style="width:36px; height:36px; background-color:#dc2626; border-radius:10px; text-align:center; vertical-align:middle;">
                  <span style="color:#fff; font-size:18px; font-weight:bold;">M</span>
                </td>
                <td style="padding-left:10px; color:#fff; font-size:20px; font-weight:800; letter-spacing:-0.5px;">
                  Recommender System
                </td>
              </tr></table>
            </td></tr>

            <!-- Icon -->
            <tr><td style="padding:24px 40px 0 40px;" align="center">
              <div style="width:56px; height:56px; border-radius:50%;
                          background:rgba(234,179,8,0.1); border:2px solid #eab308;
                          display:inline-flex; align-items:center; justify-content:center;
                          font-size:24px;">
                &#128274;
              </div>
            </td></tr>

            <!-- Title -->
            <tr><td style="padding:20px 40px 0 40px;">
              <h1 style="color:#ffffff; font-size:22px; margin:0 0 8px 0; font-weight:700; text-align:center;">
                Mat khau da duoc thay doi
              </h1>
              <p style="color:#a1a1aa; font-size:14px; line-height:1.6; margin:0; text-align:center;">
                Mat khau cua tai khoan <strong style="color:#f4f4f5;">{user_email}</strong>
                vua duoc thay doi thanh cong.<br/><br/>
                Neu ban khong thuc hien hanh dong nay, vui long lien he voi chung toi ngay lap tuc
                de bao ve tai khoan cua ban.
              </p>
            </td></tr>

            <!-- CTA Button -->
            <tr><td style="padding:28px 40px 0 40px;" align="center">
              <a href="{FRONTEND_URL}"
                 style="display:inline-block; padding:14px 40px;
                        background: linear-gradient(135deg, #dc2626, #e11d48);
                        color:#ffffff; font-size:15px; font-weight:700;
                        text-decoration:none; border-radius:10px;
                        box-shadow: 0 4px 14px rgba(220,38,38,0.35);">
                Dang nhap lai
              </a>
            </td></tr>

            <!-- Divider -->
            <tr><td style="padding:24px 40px 0 40px;">
              <div style="border-top:1px solid rgba(255,255,255,0.06);"></div>
            </td></tr>

            <!-- Footer -->
            <tr><td style="padding:16px 40px 28px 40px;">
              <p style="color:#52525b; font-size:11px; margin:0; line-height:1.5;">
                Email nay duoc gui tu dong boi he thong Recommender System de bao mat tai khoan cua ban.<br/>
                Neu ban khong yeu cau thay doi mat khau, hay doi mat khau ngay lap tuc.
              </p>
              <p style="color:#3f3f46; font-size:10px; margin:12px 0 0 0;">
                &copy; 2026 Recommender System — Hybrid AI Movie Recommender System
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


async def send_password_changed_email(user_email: str):
    """
    Gui email thong bao doi mat khau thanh cong.
    Duoc goi tu BackgroundTasks de khong block API response.
    """
    if not EMAIL_ENABLED or fast_mail is None:
        print(f"\n{'='*60}")
        print(f"[EMAIL-LOG] Password Changed Notification to: {user_email}")
        print(f"{'='*60}\n")
        return {"status": "logged", "detail": "SMTP not configured, logged to console"}

    html_body = _build_password_changed_html(user_email)

    message = MessageSchema(
        subject="[Recommender System] Mat khau cua ban vua duoc thay doi",
        recipients=[user_email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        await fast_mail.send_message(message)
        print(f"[EMAIL] Sent password-changed notification to {user_email}")
        return {"status": "sent"}
    except Exception as e:
        error_msg = str(e)
        print(f"[EMAIL ERROR] Failed to send password-changed email to {user_email}: {error_msg}")
        return {"status": "error", "detail": error_msg}


def _build_reset_password_html(reset_url: str, user_email: str) -> str:
    """Build HTML email template for password reset link."""
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0; padding:0; background-color:#09090b; font-family:'Segoe UI',Roboto,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#09090b; padding:40px 0;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0"
                 style="background-color:#18181b; border-radius:16px; overflow:hidden;
                        border:1px solid rgba(255,255,255,0.06);">

            <!-- Gradient top bar -->
            <tr><td style="height:4px; background:linear-gradient(90deg,#dc2626,#f43f5e,#f97316);"></td></tr>

            <!-- Logo -->
            <tr><td style="padding:32px 40px 0 40px;">
              <table cellpadding="0" cellspacing="0"><tr>
                <td style="width:36px; height:36px; background-color:#dc2626; border-radius:10px; text-align:center; vertical-align:middle;">
                  <span style="color:#fff; font-size:18px; font-weight:bold;">M</span>
                </td>
                <td style="padding-left:10px; color:#fff; font-size:20px; font-weight:800; letter-spacing:-0.5px;">
                  Recommender System
                </td>
              </tr></table>
            </td></tr>

            <!-- Icon -->
            <tr><td style="padding:24px 40px 0 40px;" align="center">
              <div style="width:56px; height:56px; border-radius:50%;
                          background:rgba(239,68,68,0.1); border:2px solid #ef4444;
                          display:inline-flex; align-items:center; justify-content:center;
                          font-size:24px;">
                &#128272;
              </div>
            </td></tr>

            <!-- Title -->
            <tr><td style="padding:20px 40px 0 40px;">
              <h1 style="color:#ffffff; font-size:22px; margin:0 0 8px 0; font-weight:700; text-align:center;">
                Dat lai mat khau
              </h1>
              <p style="color:#a1a1aa; font-size:14px; line-height:1.6; margin:0; text-align:center;">
                Chung toi nhan duoc yeu cau dat lai mat khau cho tai khoan
                <strong style="color:#f4f4f5;">{user_email}</strong>.<br/><br/>
                Click nut ben duoi de tao mat khau moi. Neu ban khong yeu cau, vui long bo qua email nay.
              </p>
            </td></tr>

            <!-- CTA Button -->
            <tr><td style="padding:28px 40px 0 40px;" align="center">
              <a href="{reset_url}"
                 style="display:inline-block; padding:14px 40px;
                        background: linear-gradient(135deg, #dc2626, #e11d48);
                        color:#ffffff; font-size:15px; font-weight:700;
                        text-decoration:none; border-radius:10px;
                        box-shadow: 0 4px 14px rgba(220,38,38,0.35);">
                Dat lai mat khau
              </a>
            </td></tr>

            <!-- Fallback link -->
            <tr><td style="padding:20px 40px 0 40px;">
              <p style="color:#71717a; font-size:11px; line-height:1.5; word-break:break-all;">
                Neu nut khong hoat dong, copy link sau vao trinh duyet:<br/>
                <a href="{reset_url}" style="color:#f97316; text-decoration:none;">{reset_url}</a>
              </p>
            </td></tr>

            <!-- Divider -->
            <tr><td style="padding:24px 40px 0 40px;">
              <div style="border-top:1px solid rgba(255,255,255,0.06);"></div>
            </td></tr>

            <!-- Footer -->
            <tr><td style="padding:16px 40px 28px 40px;">
              <p style="color:#52525b; font-size:11px; margin:0; line-height:1.5;">
                Link nay se het han sau <strong>15 phut</strong>.<br/>
                Neu ban khong yeu cau dat lai mat khau, vui long bo qua email nay —
                tai khoan cua ban van an toan.
              </p>
              <p style="color:#3f3f46; font-size:10px; margin:12px 0 0 0;">
                &copy; 2026 Recommender System — Hybrid AI Movie Recommender System
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


async def send_reset_password_email(user_email: str, reset_token: str):
    """
    Gui email chua link dat lai mat khau.
    Link tro ve Frontend page: FRONTEND_URL/?page=reset-password&token=xxx
    """
    reset_url = f"{FRONTEND_URL}/?page=reset-password&token={reset_token}"

    if not EMAIL_ENABLED or fast_mail is None:
        print(f"\n{'='*60}")
        print(f"[EMAIL-LOG] Password Reset Email to: {user_email}")
        print(f"[EMAIL-LOG] Reset URL: {reset_url}")
        print(f"{'='*60}\n")
        return {"status": "logged", "detail": "SMTP not configured, logged to console"}

    html_body = _build_reset_password_html(reset_url, user_email)

    message = MessageSchema(
        subject="[Recommender System] Dat lai mat khau cua ban",
        recipients=[user_email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        await fast_mail.send_message(message)
        print(f"[EMAIL] Sent password-reset email to {user_email}")
        return {"status": "sent"}
    except Exception as e:
        error_msg = str(e)
        print(f"[EMAIL ERROR] Failed to send reset email to {user_email}: {error_msg}")
        return {"status": "error", "detail": error_msg}

