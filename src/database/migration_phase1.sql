-- ============================================================
-- MIGRATION PHASE 1: Auth & User Management
-- Chạy file này MỘT LẦN trong psql hoặc pgAdmin
-- Lệnh chạy: psql -U postgres -d movie_db -f migration_phase1.sql
-- ============================================================

-- BƯỚC 1: Thêm các cột Auth vào bảng users hiện tại
-- (Bảng users đã tồn tại với user_id, gender, age, occupation, zip_code)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(10) DEFAULT 'user'
    CHECK (role IN ('admin', 'user'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(10) DEFAULT 'legacy'
    CHECK (account_type IN ('legacy', 'real'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- BƯỚC 2: Điền Email mặc định cho user cũ (legacy)
-- Format: legacy_<id>@moviedb.local => Không trùng email thật
UPDATE users
SET
    email          = 'legacy_' || user_id || '@moviedb.local',
    password_hash  = 'LEGACY_ACCOUNT_NO_LOGIN',
    role           = 'user',
    account_type   = 'legacy',
    is_active      = TRUE,
    email_verified = TRUE
WHERE email IS NULL;

-- BƯỚC 3: Thêm UNIQUE constraint cho email (nếu chưa có)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_email_unique'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);
    END IF;
END$$;

-- BƯỚC 4: Index tối ưu cho đăng nhập
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role  ON users(role);

-- BƯỚC 5: Xử lý UNIQUE constraint cho ratings (user_id, movie_id)
-- Xóa duplicate nếu có (giữ bản ghi mới nhất)
DELETE FROM ratings a
USING ratings b
WHERE a.id < b.id
  AND a.user_id = b.user_id
  AND a.movie_id = b.movie_id;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ratings_user_movie_unique'
    ) THEN
        ALTER TABLE ratings
            ADD CONSTRAINT ratings_user_movie_unique UNIQUE (user_id, movie_id);
    END IF;
END$$;

-- BƯỚC 6: Tạo bảng email verification tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id         SERIAL PRIMARY KEY,
    user_id    INT REFERENCES users(user_id) ON DELETE CASCADE,
    token      VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- BƯỚC 7: Tạo sequence cho user mới (bắt đầu từ 7001, tránh xung đột)
CREATE SEQUENCE IF NOT EXISTS users_new_id_seq
    START WITH 7001
    INCREMENT BY 1
    NO CYCLE;

-- BƯỚC 8: Kiểm tra kết quả
SELECT
    COUNT(*) FILTER (WHERE account_type = 'legacy') AS legacy_users,
    COUNT(*) FILTER (WHERE account_type = 'real')   AS real_users,
    COUNT(*) FILTER (WHERE role = 'admin')           AS admins
FROM users;
