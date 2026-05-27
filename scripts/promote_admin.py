"""Promote user 7001 to admin."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.database.db_config import DatabaseConnector

conn = DatabaseConnector.get_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET role='admin' WHERE user_id=7001 RETURNING user_id, email, role")
row = cur.fetchone()
print(f"Updated: user_id={row[0]}, email={row[1]}, role={row[2]}")
conn.commit()
cur.close()
conn.close()
