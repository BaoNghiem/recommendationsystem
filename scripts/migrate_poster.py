import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db_config import DatabaseConnector

def upgrade():
    conn = DatabaseConnector.get_connection()
    if not conn:
        print("Lỗi kết nối DB.")
        return
    cur = conn.cursor()
    try:
        print("Đang thêm cột poster_url vào bảng movies...")
        cur.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS poster_url VARCHAR(255);")
        conn.commit()
        print("Thành công!")
    except Exception as e:
        conn.rollback()
        print("Lỗi:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    upgrade()
