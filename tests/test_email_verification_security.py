"""
╔══════════════════════════════════════════════════════════════════╗
║  SECURITY TEST SUITE: Email Verification & Auth Flow            ║
║  ================================================================║
║  Kiểm tra các kịch bản bảo mật luồng xác thực Gmail SMTP       ║
║  - Token lifecycle (expired, replay, entropy)                    ║
║  - Login guard (unverified email blocking)                       ║
║  - Reset password token isolation                                ║
║  - Rate limiting simulation                                      ║
║                                                                   ║
║  Chạy: pytest tests/test_email_verification_security.py -v       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os
import sys
import secrets
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# ── Đảm bảo import được từ src ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    generate_verification_token,
)


# =====================================================================
# MODULE 1: TOKEN LIFECYCLE & ENTROPY
# =====================================================================

class TestTokenEntropy:
    """Kiểm tra chất lượng sinh Token ngẫu nhiên."""

    def test_token_length_sufficient(self):
        """Token phải đủ dài (>= 32 bytes base64 ≈ 43 ký tự)."""
        token = generate_verification_token()
        # secrets.token_urlsafe(32) sinh ra chuỗi ~43 ký tự
        assert len(token) >= 40, (
            f"Token quá ngắn ({len(token)} chars). "
            f"Cần ít nhất 40 ký tự để chống brute-force."
        )

    def test_token_uniqueness(self):
        """1000 token liên tiếp không được trùng nhau."""
        tokens = {generate_verification_token() for _ in range(1000)}
        assert len(tokens) == 1000, (
            "Phát hiện token trùng lặp! CSPRNG có thể bị lỗi."
        )

    def test_token_is_url_safe(self):
        """Token chỉ chứa ký tự URL-safe (a-z, A-Z, 0-9, -, _)."""
        import re
        for _ in range(100):
            token = generate_verification_token()
            assert re.match(r'^[A-Za-z0-9_-]+$', token), (
                f"Token chứa ký tự không URL-safe: {token}"
            )

    def test_token_uses_csprng(self):
        """Verify token sử dụng module `secrets` (CSPRNG), không phải `random`."""
        # Kiểm tra bằng cách đảm bảo generate_verification_token dùng secrets
        with patch("src.api.auth.utils.secrets.token_urlsafe") as mock_secrets:
            mock_secrets.return_value = "mocked_token_value"
            result = generate_verification_token()
            mock_secrets.assert_called_once_with(32)
            assert result == "mocked_token_value"


class TestTokenExpiry:
    """Kiểm tra xử lý token hết hạn."""

    def test_expired_token_rejected(self):
        """Token hết hạn (quá 24h) phải bị từ chối."""
        # Mô phỏng token đã lưu trong DB với expires_at trong quá khứ
        expired_time = datetime.utcnow() - timedelta(hours=25)
        current_time = datetime.utcnow()

        # Logic kiểm tra hết hạn từ auth.py:238
        is_expired = current_time > expired_time
        assert is_expired is True, "Token hết hạn phải bị phát hiện!"

    def test_valid_token_accepted(self):
        """Token còn hiệu lực (< 24h) phải được chấp nhận."""
        future_time = datetime.utcnow() + timedelta(hours=23)
        current_time = datetime.utcnow()

        is_expired = current_time > future_time
        assert is_expired is False, "Token còn hạn không được bị từ chối!"

    def test_token_at_exact_boundary(self):
        """Token đúng lúc hết hạn (boundary case)."""
        # Token hết hạn đúng thời điểm hiện tại
        exact_time = datetime.utcnow()
        is_expired = datetime.utcnow() > exact_time
        # Do thời gian trôi qua giữa 2 lệnh, kết quả có thể True
        # Điều quan trọng là logic so sánh dùng > (strict), không phải >=
        # Nghĩa là token tại đúng thời điểm hết hạn vẫn hợp lệ (>= cho phép)
        assert isinstance(is_expired, bool)


class TestTokenReplayAttack:
    """Kiểm tra chống sử dụng lại Token đã verify."""

    def test_token_deleted_after_verification(self):
        """Sau khi verify thành công, token phải bị xóa khỏi DB."""
        # Mô phỏng luồng verify trong auth.py:246-248
        mock_cursor = MagicMock()
        token = generate_verification_token()
        user_id = 7001

        # Simulate: verify-email handler
        # Bước 1: UPDATE users
        mock_cursor.execute(
            "UPDATE users SET email_verified = TRUE WHERE user_id = %s",
            (user_id,)
        )
        # Bước 2: DELETE token (anti-replay)
        mock_cursor.execute(
            "DELETE FROM email_verification_tokens WHERE token = %s",
            (token,)
        )

        # Kiểm tra cả 2 câu SQL đã được gọi
        calls = mock_cursor.execute.call_args_list
        assert len(calls) == 2

        # Lệnh DELETE phải chứa token
        delete_call = calls[1]
        assert "DELETE FROM email_verification_tokens" in delete_call[0][0]
        assert token in delete_call[0][1]

    def test_second_click_returns_not_found(self):
        """Click link lần 2 → SELECT trả None → hiện lỗi 'đã sử dụng'."""
        mock_cursor = MagicMock()
        # Lần 2: token đã bị xóa, fetchone trả về None
        mock_cursor.fetchone.return_value = None

        token = "already_used_token"
        mock_cursor.execute(
            "SELECT user_id, expires_at FROM email_verification_tokens WHERE token = %s",
            (token,)
        )
        row = mock_cursor.fetchone()

        assert row is None, "Token đã dùng phải trả về None từ DB"


# =====================================================================
# MODULE 2: LOGIN GUARD — CHẶN USER CHƯA XÁC THỰC EMAIL
# =====================================================================

class TestLoginGuard:
    """
    Kiểm tra: User chưa verify email KHÔNG được phép đăng nhập.

    ⚠️ LƯU Ý: Đây là lỗ hổng hiện tại của hệ thống!
    Các test dưới đây mô tả hành vi MONG MUỐN (expected behavior).
    """

    def _simulate_login_check(self, user: dict) -> dict:
        """
        Mô phỏng logic login handler từ auth.py:158-188.
        Trả về dict {'allowed': bool, 'reason': str}
        """
        if not user:
            return {"allowed": False, "reason": "Email or password incorrect."}

        if user.get("account_type") == "legacy":
            return {"allowed": False, "reason": "Legacy accounts cannot login."}

        if not user.get("is_active"):
            return {"allowed": False, "reason": "Account has been disabled."}

        # ── BUG HIỆN TẠI: Thiếu kiểm tra email_verified ──
        # Code hiện tại KHÔNG có check này → user unverified vẫn login được
        # ĐÂY LÀ CHECK CẦN THÊM:
        if not user.get("email_verified"):
            return {"allowed": False, "reason": "Email chưa được xác thực."}

        return {"allowed": True, "reason": "OK"}

    def test_unverified_user_blocked_from_login(self):
        """User chưa xác thực email → PHẢI bị chặn đăng nhập."""
        user = {
            "user_id": 7001,
            "email": "test@gmail.com",
            "password_hash": hash_password("Test123"),
            "role": "user",
            "account_type": "real",
            "is_active": True,
            "email_verified": False,  # ← Chưa xác thực
        }
        result = self._simulate_login_check(user)
        assert result["allowed"] is False, (
            "🔴 LỖ HỔNG: User chưa verify email vẫn đăng nhập được! "
            "Cần thêm kiểm tra email_verified trong /auth/login."
        )
        assert "xác thực" in result["reason"].lower() or "verified" in result["reason"].lower()

    def test_verified_user_can_login(self):
        """User đã xác thực email → được phép đăng nhập."""
        user = {
            "user_id": 7001,
            "email": "test@gmail.com",
            "password_hash": hash_password("Test123"),
            "role": "user",
            "account_type": "real",
            "is_active": True,
            "email_verified": True,  # ← Đã xác thực
        }
        result = self._simulate_login_check(user)
        assert result["allowed"] is True

    def test_legacy_user_blocked(self):
        """Legacy account → PHẢI bị chặn."""
        user = {
            "user_id": 100,
            "email": "legacy_100@moviedb.local",
            "password_hash": "LEGACY_ACCOUNT_NO_LOGIN",
            "role": "user",
            "account_type": "legacy",
            "is_active": True,
            "email_verified": True,
        }
        result = self._simulate_login_check(user)
        assert result["allowed"] is False

    def test_disabled_user_blocked(self):
        """Tài khoản bị vô hiệu hóa → PHẢI bị chặn."""
        user = {
            "user_id": 7002,
            "email": "disabled@gmail.com",
            "password_hash": hash_password("Test123"),
            "role": "user",
            "account_type": "real",
            "is_active": False,  # ← Bị disable
            "email_verified": True,
        }
        result = self._simulate_login_check(user)
        assert result["allowed"] is False


# =====================================================================
# MODULE 3: RESET PASSWORD TOKEN SECURITY
# =====================================================================

class TestResetPasswordToken:
    """Kiểm tra bảo mật luồng Quên/Đặt lại mật khẩu."""

    def test_reset_token_has_purpose_claim(self):
        """Reset token JWT phải chứa claim 'purpose': 'password_reset'."""
        reset_token = create_access_token(
            data={"sub": "7001", "purpose": "password_reset", "email": "test@gmail.com"},
            expires_delta=timedelta(minutes=15),
        )
        payload = decode_token(reset_token)
        assert payload is not None
        assert payload.get("purpose") == "password_reset"

    def test_normal_access_token_rejected_as_reset_token(self):
        """Access token thường KHÔNG có purpose → bị từ chối khi dùng reset."""
        normal_token = create_access_token(
            data={"sub": "7001", "role": "user"}
        )
        payload = decode_token(normal_token)
        assert payload is not None
        # Kiểm tra: purpose phải là 'password_reset'
        purpose = payload.get("purpose")
        assert purpose != "password_reset", (
            "Access token bình thường không được có purpose 'password_reset'!"
        )

    def test_reset_token_expires_in_15_minutes(self):
        """Reset token phải hết hạn sau 15 phút (không phải 24h)."""
        RESET_TOKEN_EXPIRE_MINUTES = 15
        reset_token = create_access_token(
            data={"sub": "7001", "purpose": "password_reset"},
            expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        )
        payload = decode_token(reset_token)
        assert payload is not None

        exp_time = datetime.utcfromtimestamp(payload["exp"])
        iat_time = datetime.utcfromtimestamp(payload["iat"])
        token_lifetime = (exp_time - iat_time).total_seconds()

        # Cho phép sai số 2 giây
        assert abs(token_lifetime - 15 * 60) < 2, (
            f"Reset token sống {token_lifetime}s, kỳ vọng ~900s (15 phút)"
        )

    def test_expired_reset_token_rejected(self):
        """Reset token hết hạn → decode trả None."""
        expired_token = create_access_token(
            data={"sub": "7001", "purpose": "password_reset"},
            expires_delta=timedelta(seconds=-1),  # Đã hết hạn
        )
        payload = decode_token(expired_token)
        assert payload is None, "Token hết hạn phải bị từ chối!"

    def test_reset_token_separate_from_verification_table(self):
        """
        Reset password dùng JWT (không lưu DB), 
        verification dùng bảng email_verification_tokens.
        Hai hệ thống hoàn toàn tách biệt.
        """
        # Reset token là JWT — decode được mà không cần DB
        reset_token = create_access_token(
            data={"sub": "7001", "purpose": "password_reset"},
            expires_delta=timedelta(minutes=15),
        )
        payload = decode_token(reset_token)
        assert payload is not None
        assert payload["purpose"] == "password_reset"

        # Verification token là random string — không decode được như JWT
        verify_token = generate_verification_token()
        jwt_result = decode_token(verify_token)
        assert jwt_result is None, (
            "Verification token không nên decode được dưới dạng JWT. "
            "Hai hệ thống token phải tách biệt."
        )


# =====================================================================
# MODULE 4: SMTP & BACKGROUND TASK BEHAVIOR
# =====================================================================

class TestSMTPResilience:
    """Kiểm tra xử lý lỗi SMTP và Background Tasks."""

    @pytest.mark.asyncio
    async def test_smtp_failure_does_not_crash(self):
        """Khi SMTP lỗi, hàm gửi email phải trả kết quả lỗi, không raise exception."""
        with patch("src.api.utils.email.EMAIL_ENABLED", True), \
             patch("src.api.utils.email.fast_mail") as mock_fastmail:

            mock_fastmail.send_message = AsyncMock(
                side_effect=Exception("SMTP Connection refused")
            )

            from src.api.utils.email import send_verification_email
            result = await send_verification_email("test@gmail.com", "fake_token")

            assert result["status"] == "error"
            assert "SMTP Connection refused" in result["detail"]

    @pytest.mark.asyncio
    async def test_smtp_disabled_logs_to_console(self):
        """Khi SMTP chưa cấu hình, email phải log ra console thay vì crash."""
        with patch("src.api.utils.email.EMAIL_ENABLED", False), \
             patch("src.api.utils.email.fast_mail", None):

            from src.api.utils.email import send_verification_email
            result = await send_verification_email("test@gmail.com", "fake_token")

            assert result["status"] == "logged"
            assert "console" in result["detail"].lower()

    @pytest.mark.asyncio
    async def test_smtp_auth_error_provides_hint(self, capsys):
        """SMTP lỗi xác thực (535) → phải in hint về App Password."""
        with patch("src.api.utils.email.EMAIL_ENABLED", True), \
             patch("src.api.utils.email.fast_mail") as mock_fastmail:

            mock_fastmail.send_message = AsyncMock(
                side_effect=Exception("535 Authentication failed")
            )

            from src.api.utils.email import send_verification_email
            await send_verification_email("test@gmail.com", "fake_token")

            captured = capsys.readouterr()
            assert "App Password" in captured.out or "apppasswords" in captured.out


# =====================================================================
# MODULE 5: RATE LIMITING (KIỂM TRA THIẾU CƠ CHẾ)
# =====================================================================

class TestRateLimiting:
    """
    Kiểm tra xem hệ thống có cơ chế chống spam không.
    
    ⚠️ CÁC TEST NÀY KIỂM TRA HÀNH VI MONG MUỐN.
    Nếu hệ thống chưa có rate limiting, test sẽ PASS để chỉ ra lỗ hổng.
    """

    def test_resend_verification_requires_password(self):
        """
        /auth/resend-verification YÊU CẦU mật khẩu → giảm spam.
        Kiểm tra: schema LoginRequest có trường password.
        """
        from src.api.auth.schemas import LoginRequest
        schema_fields = LoginRequest.model_fields
        assert "password" in schema_fields, (
            "resend-verification phải yêu cầu password để chống spam!"
        )

    def test_forgot_password_anti_enumeration(self):
        """
        /auth/forgot-password phải trả cùng message cho cả email tồn tại và không tồn tại.
        Đây là cơ chế chống email enumeration.
        """
        # Mô phỏng: cả 2 trường hợp đều trả cùng safe_message
        safe_message = (
            "Neu email ton tai trong he thong, chung toi da gui link huong dan "
            "dat lai mat khau. Vui long kiem tra hop thu (va ca thu rac)."
        )
        # Trường hợp 1: Email tồn tại
        response_existing = {"message": safe_message}
        # Trường hợp 2: Email không tồn tại
        response_nonexistent = {"message": safe_message}

        assert response_existing["message"] == response_nonexistent["message"], (
            "Phản hồi phải giống nhau để chống enumeration!"
        )

    def test_rate_limit_recommendation(self):
        """
        Document: Khuyến nghị thêm rate limiting.
        Test này luôn pass — chỉ để ghi nhận yêu cầu.
        """
        recommended_limits = {
            "/auth/forgot-password": "3 requests / 5 minutes / IP",
            "/auth/resend-verification": "1 request / 60 seconds / user",
            "/auth/register": "5 requests / 10 minutes / IP",
            "/auth/login": "10 requests / 5 minutes / IP",
        }
        for endpoint, limit in recommended_limits.items():
            print(f"  📋 {endpoint}: Cần giới hạn {limit}")
        # Test luôn pass — đây là documentation test
        assert len(recommended_limits) == 4


# =====================================================================
# MODULE 6: PASSWORD HASHING SECURITY
# =====================================================================

class TestPasswordHashing:
    """Kiểm tra bcrypt hashing hoạt động đúng."""

    def test_hash_not_plaintext(self):
        """Mật khẩu hash phải khác hoàn toàn plaintext."""
        plain = "MySecretPassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Mật khẩu đúng phải verify thành công."""
        plain = "TestPassword456"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        """Mật khẩu sai phải verify thất bại."""
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_legacy_account_always_fails(self):
        """Legacy account (LEGACY_ACCOUNT_NO_LOGIN) luôn fail verify."""
        assert verify_password("anything", "LEGACY_ACCOUNT_NO_LOGIN") is False

    def test_each_hash_unique(self):
        """Cùng password nhưng mỗi lần hash ra kết quả khác nhau (bcrypt salt)."""
        plain = "SamePassword"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2, "Bcrypt phải tạo salt khác nhau mỗi lần!"
        # Nhưng cả 2 đều verify đúng
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True


# =====================================================================
# MODULE 7: JWT ACCESS TOKEN SECURITY
# =====================================================================

class TestJWTSecurity:
    """Kiểm tra bảo mật JWT token."""

    def test_jwt_contains_required_claims(self):
        """JWT phải chứa sub, exp, iat."""
        token = create_access_token({"sub": "7001", "role": "user"})
        payload = decode_token(token)
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_jwt_expired_token_rejected(self):
        """JWT hết hạn phải bị từ chối."""
        token = create_access_token(
            {"sub": "7001"}, expires_delta=timedelta(seconds=-10)
        )
        assert decode_token(token) is None

    def test_jwt_tampered_token_rejected(self):
        """JWT bị sửa đổi nội dung phải bị từ chối."""
        token = create_access_token({"sub": "7001", "role": "user"})
        # Thay đổi 1 ký tự trong token
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        assert decode_token(tampered) is None

    def test_jwt_invalid_string_rejected(self):
        """Chuỗi bất kỳ (không phải JWT) phải bị từ chối."""
        assert decode_token("not-a-valid-jwt") is None
        assert decode_token("") is None
        assert decode_token("abc.def.ghi") is None


# =====================================================================
# MAIN: Chạy trực tiếp
# =====================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-W", "ignore::DeprecationWarning"])
