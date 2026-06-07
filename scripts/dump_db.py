"""
scripts/dump_db.py
==================
Xuất toàn bộ dữ liệu PostgreSQL (movie_db) ra file SQL.
Chạy lệnh này để tạo snapshot DB trước khi push lên GitHub:

    python scripts/dump_db.py

File kết quả: scripts/movie_db_dump.sql
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Fix encoding Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

def dump_db():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "movie_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")

    out_file = BASE_DIR / "scripts" / "movie_db_dump.sql"

    print(f"[DUMP] Exporting DB: {db_name}@{db_host}:{db_port}")
    print(f"[DUMP] Output: {out_file.name} (in scripts/)")

    env = os.environ.copy()
    env["PGPASSWORD"] = db_pass

    cmd = [
        "pg_dump",
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "--no-owner",           # Bỏ qua owner (dễ restore trên máy khác)
        "--no-acl",             # Bỏ qua permissions
        "-f", str(out_file),
    ]

    try:
        result = subprocess.run(cmd, env=env, check=True,
                                capture_output=True, text=True)
        size_mb = out_file.stat().st_size / 1_048_576
        print(f"[DUMP] Thanh cong! File: {size_mb:.1f} MB")
        print(f"[DUMP] Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n[DONE] De restore tren may khac, chay:")
        print(f"       python scripts/restore_db.py")
    except FileNotFoundError:
        print("[ERROR] pg_dump khong tim thay. Hay cai PostgreSQL client tools.")
        print("        Windows: cai PostgreSQL tu postgresql.org la co san pg_dump")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Dump that bai: {e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    dump_db()
