import sys; sys.path.insert(0, r"j:\Bài đồ án")
from src.database.db_config import DatabaseConnector
conn = DatabaseConnector.get_connection()
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position")
print([r[0] for r in cur.fetchall()])
cur.close(); conn.close()
