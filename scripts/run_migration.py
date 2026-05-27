"""
Script chạy Migration Phase 2 — thêm cột Auth vào bảng users
Chạy: python run_migration.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db_config import DatabaseConnector

conn = DatabaseConnector.get_connection()
if not conn:
    print('ERROR: Cannot connect to DB')
    sys.exit(1)

cur = conn.cursor()

steps = [
    ('Add email',          'ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)'),
    ('Add password_hash',  'ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT'),
    ('Add role',           "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(10) DEFAULT 'user'"),
    ('Add account_type',   "ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(10) DEFAULT 'legacy'"),
    ('Add is_active',      'ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'),
    ('Add email_verified', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE'),
    ('Add created_at',     'ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()'),
]

for name, sql in steps:
    try:
        cur.execute(sql)
        conn.commit()
        print(f'  OK : {name}')
    except Exception as e:
        conn.rollback()
        print(f'  SKIP: {name} — {e}')

# Điền data cho legacy users
try:
    cur.execute("""
        UPDATE users
        SET email          = 'legacy_' || user_id || '@moviedb.local',
            password_hash  = 'LEGACY_ACCOUNT_NO_LOGIN',
            role           = 'user',
            account_type   = 'legacy',
            is_active      = TRUE,
            email_verified = TRUE
        WHERE email IS NULL
    """)
    n = cur.rowcount
    conn.commit()
    print(f'  OK : Updated {n} legacy users with placeholder email')
except Exception as e:
    conn.rollback()
    print(f'  SKIP legacy update: {e}')

# UNIQUE email
try:
    cur.execute('ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email)')
    conn.commit()
    print('  OK : UNIQUE constraint users.email')
except Exception as e:
    conn.rollback()
    print(f'  SKIP email unique: {e}')

# Index email
try:
    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    conn.commit()
    print('  OK : INDEX users.email')
except Exception as e:
    conn.rollback()
    print(f'  SKIP idx email: {e}')

# Dedup ratings
try:
    cur.execute("""
        DELETE FROM ratings a
        USING ratings b
        WHERE a.id < b.id
          AND a.user_id  = b.user_id
          AND a.movie_id = b.movie_id
    """)
    n = cur.rowcount
    conn.commit()
    print(f'  OK : Removed {n} duplicate ratings')
except Exception as e:
    conn.rollback()
    print(f'  SKIP dedup ratings: {e}')

# UNIQUE ratings(user_id, movie_id)
try:
    cur.execute('ALTER TABLE ratings ADD CONSTRAINT ratings_user_movie_unique UNIQUE (user_id, movie_id)')
    conn.commit()
    print('  OK : UNIQUE ratings(user_id, movie_id)')
except Exception as e:
    conn.rollback()
    print(f'  SKIP ratings unique: {e}')

# Email verification table
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id         SERIAL PRIMARY KEY,
            user_id    INT REFERENCES users(user_id) ON DELETE CASCADE,
            token      VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    print('  OK : Table email_verification_tokens')
except Exception as e:
    conn.rollback()
    print(f'  SKIP token table: {e}')

# Sequence user mới từ 7001
try:
    cur.execute('CREATE SEQUENCE IF NOT EXISTS users_new_id_seq START WITH 7001 INCREMENT BY 1 NO CYCLE')
    conn.commit()
    print('  OK : Sequence users_new_id_seq (start=7001)')
except Exception as e:
    conn.rollback()
    print(f'  SKIP sequence: {e}')

# Kiểm tra kết quả
cur.execute("SELECT COUNT(*) FILTER(WHERE account_type='legacy'), COUNT(*) FILTER(WHERE account_type='real') FROM users")
legacy, real = cur.fetchone()
print(f'\n=== MIGRATION DONE ===')
print(f'  Legacy users : {legacy}')
print(f'  Real users   : {real}')

cur.close()
conn.close()
