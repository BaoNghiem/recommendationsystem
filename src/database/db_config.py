import os
import sys
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 on Windows to prevent charmap errors with Vietnamese text
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass


class DatabaseConnector:
    """
    Quản lý kết nối PostgreSQL với Connection Pooling.
    Pool tái sử dụng connections thay vì tạo mới mỗi request,
    tránh quá tải khi nhiều user truy cập cùng lúc.
    """
    HOST     = os.getenv("DB_HOST",     "localhost")
    PORT     = os.getenv("DB_PORT",     "5432")
    DATABASE = os.getenv("DB_NAME",     "movie_db")
    USER     = os.getenv("DB_USER",     "postgres")
    PASSWORD = os.getenv("DB_PASSWORD", "b")

    # Connection Pool (khoi tao 1 lan, tai su dung xuyen suot)
    _pool = None

    @classmethod
    def _init_pool(cls, minconn=2, maxconn=20):
        """Khoi tao connection pool (chi chay 1 lan duy nhat)."""
        try:
            cls._pool = pool.ThreadedConnectionPool(
                minconn, maxconn,
                host=cls.HOST,
                port=cls.PORT,
                database=cls.DATABASE,
                user=cls.USER,
                password=cls.PASSWORD,
            )
            print(f"[DB] Connection Pool initialized: min={minconn}, max={maxconn}")
        except Exception as e:
            print(f"CRITICAL ERROR: Cannot create connection pool: {e}")
            cls._pool = None

    @classmethod
    def get_connection(cls):
        """Lay connection truc tiep (tranh loi pool exhausted vi cac route deu goi conn.close())."""
        try:
            return psycopg2.connect(
                host=cls.HOST, port=cls.PORT,
                database=cls.DATABASE, user=cls.USER,
                password=cls.PASSWORD,
            )
        except Exception as e:
            print(f"CRITICAL ERROR: Cannot connect to PostgreSQL: {e}")
            return None

    @classmethod
    def return_connection(cls, conn):
        """Tra connection ve pool de tai su dung."""
        if cls._pool and conn:
            try:
                cls._pool.putconn(conn)
            except Exception:
                pass

    @classmethod
    def test_connection(cls):
        conn = cls.get_connection()
        if conn:
            print(f"--- KET NOI THANH CONG: {cls.DATABASE} ---")
            conn.close()
            return True
        return False

