import sys
sys.path.append('.')
from src.database.db_config import DatabaseConnector
import bcrypt

password = 'admin2004'
email = 'nghiemlybao2004@gmail.com'
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

conn = DatabaseConnector.get_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed, email))
conn.commit()
print(f'[OK] Password reset to "{password}" for {email}')
print(f'     Rows affected: {cur.rowcount}')
cur.close()
conn.close()
