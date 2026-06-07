"""
scripts/restore_db.py
=====================
Restore database từ file dump SQL (tạo bởi dump_db.py).
Chạy trên máy mới sau khi clone repo:

    1. Tao database trong PostgreSQL:
       createdb -U postgres movie_db

    2. Chay script nay:
       python scripts/restore_db.py

Luu y: PostgreSQL phai dang chay va da tao DB 'movie_db' truoc.
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

def restore_db():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "movie_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")

    dump_file = BASE_DIR / "scripts" / "movie_db_dump.sql"

    if not dump_file.exists():
        print(f"[ERROR] Khong tim thay file dump: {dump_file}")
        print("[ERROR] Hay chay 'python scripts/dump_db.py' tren may goc truoc.")
        sys.exit(1)

    size_mb = dump_file.stat().st_size / 1_048_576
    print(f"[RESTORE] File dump: {dump_file} ({size_mb:.1f} MB)")
    print(f"[RESTORE] Target DB: {db_name}@{db_host}:{db_port}")
    print(f"[RESTORE] Dang restore... (co the mat vai phut)")

    env = os.environ.copy()
    env["PGPASSWORD"] = db_pass

    cmd = [
        "psql",
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "-f", str(dump_file),
        "-q",   # quiet mode
    ]

    try:
        result = subprocess.run(cmd, env=env, check=True,
                                capture_output=True, text=True)
        print("[RESTORE] Thanh cong! Database da duoc restore.")
        if result.stderr:
            # Mot so warning la binh thuong khi restore
            warnings = [l for l in result.stderr.split("\n") if l.strip() and "WARNING" in l.upper()]
            if warnings:
                print(f"[RESTORE] {len(warnings)} warnings (binh thuong, co the bo qua):")
                for w in warnings[:5]:
                    print(f"   {w}")
        print(f"\n[NEXT] Cac buoc tiep theo:")
        print(f"   1. Copy .env.example -> .env va dien thong tin")
        print(f"   2. pip install -r requirements.txt")
        print(f"   3. uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload")
        print(f"   4. cd frontend && npm install && npm run dev")
    except FileNotFoundError:
        print("[ERROR] psql khong tim thay. Hay cai PostgreSQL client tools.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Restore that bai:")
        print(e.stderr)
        sys.exit(1)


if __name__ == "__main__":
    restore_db()
