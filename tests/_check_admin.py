import sys
sys.path.insert(0, r"j:\Bài đồ án")
from src.database.db_config import DatabaseConnector
conn = DatabaseConnector.get_connection()
cur = conn.cursor()
cur.execute("SELECT user_id, email, role, account_type FROM users WHERE role = 'admin'")
rows = cur.fetchall()
print("Admin accounts:", rows)
cur.close()
conn.close()
