"""
Phase 2: SVD Fold-In Audit - Cold User + Anime Rating + Recommendation Quality
===============================================================================
"""
import sys, os, time, json, requests
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE = "http://127.0.0.1:8000"
results = []

def TEST(name, passed, detail=""):
    s = "PASS" if passed else "FAIL"
    results.append({"test": name, "status": s, "detail": detail, "phase": 2})
    print(f"  [{'OK' if passed else 'XX'}] {name}" + (f" | {detail}" if detail else ""))

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# Load phase1 results
p1_path = Path(__file__).parent / "phase1_results.json"
p1 = {}
if p1_path.exists():
    p1 = json.loads(p1_path.read_text(encoding="utf-8"))
inserted_ids = p1.get("inserted_movie_ids", [])
admin_token = p1.get("admin_token")
ADMIN_H = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

# ══════════════════════════════════════════════════════════════
# 2.1 Create Cold User
# ══════════════════════════════════════════════════════════════
section("2.1 Create Cold User (Anime Fan)")

from src.database.db_config import DatabaseConnector

ts = int(time.time())
cold_email = f"anime_fan_{ts}@test.com"
cold_token = None
cold_uid = None

try:
    r = requests.post(f"{BASE}/auth/register", json={"email": cold_email, "password": "anime123456"})
    TEST("Register cold user", r.status_code == 201, f"HTTP {r.status_code}")

    # Force verify
    conn = DatabaseConnector.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (cold_email,))
    conn.commit()
    cur.close(); conn.close()

    r = requests.post(f"{BASE}/auth/login", json={"email": cold_email, "password": "anime123456"})
    if r.status_code == 200:
        cold_token = r.json()["access_token"]
        cold_uid = r.json()["user_id"]
        TEST("Login cold user", True, f"user_id={cold_uid}")
    else:
        TEST("Login cold user", False, r.text[:200])
except Exception as e:
    TEST("Create cold user", False, str(e))

COLD_H = {"Authorization": f"Bearer {cold_token}"} if cold_token else {}

# ══════════════════════════════════════════════════════════════
# 2.2 Pydantic Validation on /rate
# ══════════════════════════════════════════════════════════════
section("2.2 Pydantic Validation (Rating Bounds)")

if cold_token:
    test_mid = inserted_ids[0] if inserted_ids else 1
    # Rating too high
    r = requests.post(f"{BASE}/rate", headers=COLD_H, json={"movie_id": test_mid, "rating": 6.0})
    TEST("Rating > 5.0 rejected", r.status_code == 422, f"HTTP {r.status_code}")

    # Rating too low
    r = requests.post(f"{BASE}/rate", headers=COLD_H, json={"movie_id": test_mid, "rating": 0.0})
    TEST("Rating < 0.5 rejected", r.status_code == 422, f"HTTP {r.status_code}")

    # Valid rating
    r = requests.post(f"{BASE}/rate", headers=COLD_H, json={"movie_id": test_mid, "rating": 5.0})
    TEST("Rating 5.0 accepted", r.status_code == 200, f"HTTP {r.status_code}")

    # No JWT
    r = requests.post(f"{BASE}/rate", json={"movie_id": test_mid, "rating": 4.0})
    TEST("/rate without JWT => 401", r.status_code in (401, 403), f"HTTP {r.status_code}")
else:
    TEST("Pydantic validation skipped", False, "No cold user token")

# ══════════════════════════════════════════════════════════════
# 2.3 Rate 7 Anime/Animation movies (5 stars each)
# ══════════════════════════════════════════════════════════════
section("2.3 Rate 7 Anime/Animation Movies (5 stars)")

# Find animation movies from seeded data
anime_keywords = ["Spirited Away", "Princess Mononoke", "My Neighbor Totoro",
                  "Howl's Moving Castle", "Your Name", "A Silent Voice", "Suzume"]

anime_ids_rated = []
if cold_token and inserted_ids:
    # Find these movies in DB
    conn = DatabaseConnector.get_connection()
    cur = conn.cursor()
    for kw in anime_keywords:
        cur.execute("SELECT movie_id FROM movies WHERE title ILIKE %s LIMIT 1", (f"%{kw}%",))
        row = cur.fetchone()
        if row:
            anime_ids_rated.append(row[0])
    cur.close(); conn.close()

    rated_count = 0
    for mid in anime_ids_rated[:7]:
        r = requests.post(f"{BASE}/rate", headers=COLD_H,
                          json={"movie_id": mid, "rating": 5.0})
        if r.status_code == 200:
            rated_count += 1

    TEST(f"Rated {rated_count}/7 anime movies", rated_count >= 5,
         f"movie_ids={anime_ids_rated[:7]}")

# ══════════════════════════════════════════════════════════════
# 2.4 Fold-In Audit: Get Recommendations
# ══════════════════════════════════════════════════════════════
section("2.4 Fold-In Audit: /recommend/{user_id}")

if cold_uid and cold_token:
    # BUG B FIX: Them Authorization header (COLD_H) de pass JWT guard
    r = requests.get(f"{BASE}/recommend/{cold_uid}", headers=COLD_H)
    if r.status_code == 200:
        data = r.json()
        strategy = data.get("strategy", "")
        recs = data.get("recommendations", [])

        TEST("Recommendations returned", len(recs) > 0, f"{len(recs)} movies")
        TEST("Strategy is fold-in or content-based",
             strategy in ("hybrid_foldin", "content_based"),
             f"strategy='{strategy}'")

        # Audit: Check if recommended movies share Animation genre
        animation_count = 0
        for rec in recs[:10]:
            g = rec.get("genres_orig", "")
            if "Animation" in g:
                animation_count += 1

        pct = (animation_count / min(len(recs), 10)) * 100 if recs else 0
        TEST("Top-10 recs have Animation affinity",
             animation_count >= 3,
             f"{animation_count}/10 = {pct:.0f}% Animation")

        # Check predicted ratings
        pred_ratings = [rec.get("predicted_rating", 0) for rec in recs[:10]]
        if pred_ratings:
            avg_pred = sum(pred_ratings) / len(pred_ratings)
            TEST("Avg predicted rating > 3.0", avg_pred > 3.0,
                 f"avg={avg_pred:.2f}")

        # Log top 5 for manual review
        print("\n  --- Top 5 Recommendations (Manual Review) ---")
        for i, rec in enumerate(recs[:5]):
            print(f"    {i+1}. [{rec.get('movie_id')}] {rec.get('title')} "
                  f"| {rec.get('genres_orig')} | pred={rec.get('predicted_rating')}")
    else:
        TEST("GET /recommend", False, f"HTTP {r.status_code}: {r.text[:200]}")
else:
    TEST("Fold-in audit skipped", False, "No cold user")

# Save results
out_path = Path(__file__).parent / "phase2_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "results": results,
        "cold_uid": cold_uid,
        "cold_email": cold_email,
        "cold_token": cold_token,   # BUG B FIX: Luu token de phase4 su dung
        "anime_ids_rated": anime_ids_rated,
    }, f, ensure_ascii=False, indent=2)

section("PHASE 2 SUMMARY")
p = sum(1 for r in results if r["status"] == "PASS")
f_ = sum(1 for r in results if r["status"] == "FAIL")
print(f"  PASSED: {p}/{len(results)}  |  FAILED: {f_}")
print(f"  Cold user: {cold_uid} ({cold_email})")
print(f"  Results saved: {out_path}")
