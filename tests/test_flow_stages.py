"""
Test tung giai doan cua Recommendation Flow voi 1 tai khoan rac moi.
GD1: No data -> Popularity
GD2: 1-4 ratings (>= 4 sao) -> Content-Based
GD3: >= 5 ratings -> Fold-in SVD
GD4: Sau retrain -> SVD thuan (hybrid)
"""
import sys, os, time, requests, json
sys.path.insert(0, r"j:\Bài đồ án")
os.environ["PYTHONIOENCODING"] = "utf-8"

BASE = "http://127.0.0.1:8000"
EMAIL = f"test_flow_{int(time.time())}@test.com"
PASSWORD = "TestFlow123"

def section(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

def show_recs(data, max_show=5):
    strategy = data.get("strategy", "?")
    recs = data.get("recommendations", [])
    explanation = data.get("explanation", "")
    print(f"  Strategy: {strategy}")
    print(f"  Explanation: {explanation}")
    print(f"  So phim goi y: {len(recs)}")
    for i, r in enumerate(recs[:max_show]):
        print(f"    {i+1}. [{r.get('movie_id')}] {r.get('title','?')} "
              f"| {r.get('genres_orig','')} | pred={r.get('predicted_rating','?')}")
    if len(recs) > max_show:
        print(f"    ... va {len(recs) - max_show} phim nua")
    return strategy

# ═══════════════════════════════════════════════════
# BUOC 0: Dang ky tai khoan rac
# ═══════════════════════════════════════════════════
section("BUOC 0: Dang ky tai khoan rac")
r = requests.post(f"{BASE}/auth/register", json={"email": EMAIL, "password": PASSWORD})
print(f"  Register: HTTP {r.status_code}")
if r.status_code not in (200, 201):
    print(f"  ERROR: {r.text}")
    sys.exit(1)

# Verify email (bypass) trong DB
from src.database.db_config import DatabaseConnector
conn = DatabaseConnector.get_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s RETURNING user_id", (EMAIL,))
user_id = cur.fetchone()[0]
conn.commit()
cur.close(); conn.close()
print(f"  User ID: {user_id}")
print(f"  Email: {EMAIL}")

# Login
r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"  Login OK, token len={len(token)}")

# ═══════════════════════════════════════════════════
# GIAI DOAN 1: Khong co data -> Popularity
# ═══════════════════════════════════════════════════
section("GIAI DOAN 1: User CHUA co rating -> Ky vong: POPULARITY")
r = requests.get(f"{BASE}/recommend/{user_id}")
data = r.json()
s1 = show_recs(data)
result1 = "PASS" if s1 == "popularity" else "FAIL"
print(f"\n  >>> KET QUA: {result1} (strategy={s1}, ky vong=popularity)")

# ═══════════════════════════════════════════════════
# GIAI DOAN 2: Rate 3 phim (>= 4 sao) -> Content-Based
# ═══════════════════════════════════════════════════
section("GIAI DOAN 2: Rate 3 phim (>= 4 sao) -> Ky vong: CONTENT-BASED")
# Rate 3 phim Action
test_movies = [
    (260, 5.0),   # Star Wars IV
    (1196, 4.5),  # Star Wars V
    (1210, 4.0),  # Star Wars VI
]
for mid, rating in test_movies:
    r = requests.post(f"{BASE}/rate", json={"movie_id": mid, "rating": rating}, headers=headers)
    status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
    print(f"  Rate movie {mid} = {rating} -> {status}")

time.sleep(0.5)
r = requests.get(f"{BASE}/recommend/{user_id}")
data = r.json()
s2 = show_recs(data)
result2 = "PASS" if s2 == "content_based" else "FAIL"
print(f"\n  >>> KET QUA: {result2} (strategy={s2}, ky vong=content_based)")

# ═══════════════════════════════════════════════════
# GIAI DOAN 3: Rate them 5 phim nua (tong >= 5) -> Fold-in SVD
# ═══════════════════════════════════════════════════
section("GIAI DOAN 3: Rate them phim (tong >= 5) -> Ky vong: HYBRID_FOLDIN")
extra_movies = [
    (2571, 5.0),  # Matrix
    (1198, 4.5),  # Raiders of the Lost Ark
    (593, 4.0),   # Silence of the Lambs
    (2028, 3.5),  # Saving Private Ryan
    (1580, 4.5),  # Men in Black
]
for mid, rating in extra_movies:
    r = requests.post(f"{BASE}/rate", json={"movie_id": mid, "rating": rating}, headers=headers)
    status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
    print(f"  Rate movie {mid} = {rating} -> {status}")

time.sleep(0.5)
r = requests.get(f"{BASE}/recommend/{user_id}")
data = r.json()
s3 = show_recs(data)
result3 = "PASS" if s3 == "hybrid_foldin" else "FAIL"
print(f"\n  >>> KET QUA: {result3} (strategy={s3}, ky vong=hybrid_foldin)")

# ═══════════════════════════════════════════════════
# TONG KET
# ═══════════════════════════════════════════════════
section("TONG KET KIEM TRA FLOW GOI Y")
print(f"  GD1 (No data -> Popularity):         {result1}")
print(f"  GD2 (3 ratings -> Content-Based):     {result2}")
print(f"  GD3 (8 ratings -> Fold-in SVD):       {result3}")
print(f"  GD4 (Sau retrain -> SVD thuan):       Can chay retrain rieng")
print(f"\n  User ID: {user_id} | Email: {EMAIL}")
print(f"  (De test GD4, chay auto_generate_and_retrain.py roi restart backend)")
