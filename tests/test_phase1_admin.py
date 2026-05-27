"""
Phase 1: Admin Authentication, RBAC, and Bulk Movie Seed (100 movies)
=====================================================================
"""
import sys, os, time, json, requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE = "http://127.0.0.1:8000"
results = []

def TEST(name, passed, detail=""):
    s = "PASS" if passed else "FAIL"
    results.append({"test": name, "status": s, "detail": detail, "phase": 1})
    print(f"  [{'OK' if passed else 'XX'}] {name}" + (f" | {detail}" if detail else ""))

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ══════════════════════════════════════════════════════════════
# 100 Real Movies to Seed
# ══════════════════════════════════════════════════════════════
MOVIES_SEED = [
    ("Spider-Man: Across the Spider-Verse (2023)", "Animation|Action|Adventure"),
    ("Oppenheimer (2023)", "Drama|Thriller"),
    ("Barbie (2023)", "Comedy|Fantasy"),
    ("The Super Mario Bros. Movie (2023)", "Animation|Adventure|Comedy"),
    ("Guardians of the Galaxy Vol. 3 (2023)", "Action|Adventure|Sci-Fi"),
    ("John Wick: Chapter 4 (2023)", "Action|Thriller"),
    ("Killers of the Flower Moon (2023)", "Crime|Drama|Mystery"),
    ("Past Lives (2023)", "Romance|Drama"),
    ("Poor Things (2023)", "Comedy|Drama|Romance"),
    ("The Holdovers (2023)", "Comedy|Drama"),
    ("Anatomy of a Fall (2023)", "Drama|Thriller|Mystery"),
    ("Saltburn (2023)", "Drama|Thriller"),
    ("The Boy and the Heron (2023)", "Animation|Adventure|Fantasy"),
    ("Elemental (2023)", "Animation|Comedy|Fantasy"),
    ("Mission: Impossible - Dead Reckoning Part One (2023)", "Action|Adventure|Thriller"),
    ("Indiana Jones and the Dial of Destiny (2023)", "Action|Adventure"),
    ("Napoleon (2023)", "Drama|War"),
    ("The Creator (2023)", "Action|Sci-Fi|Thriller"),
    ("Wonka (2023)", "Comedy|Fantasy|Musical"),
    ("Wish (2023)", "Animation|Comedy|Fantasy"),
    ("Dune: Part Two (2024)", "Action|Adventure|Sci-Fi"),
    ("Inside Out 2 (2024)", "Animation|Comedy|Drama"),
    ("Deadpool & Wolverine (2024)", "Action|Comedy|Sci-Fi"),
    ("Furiosa: A Mad Max Saga (2024)", "Action|Adventure|Sci-Fi"),
    ("The Fall Guy (2024)", "Action|Comedy"),
    ("Kung Fu Panda 4 (2024)", "Animation|Action|Comedy"),
    ("Godzilla x Kong: The New Empire (2024)", "Action|Adventure|Sci-Fi"),
    ("Ghostbusters: Frozen Empire (2024)", "Comedy|Fantasy|Adventure"),
    ("Civil War (2024)", "Action|Drama|Thriller"),
    ("Challengers (2024)", "Drama|Romance"),
    ("Alien: Romulus (2024)", "Horror|Sci-Fi|Thriller"),
    ("Beetlejuice Beetlejuice (2024)", "Comedy|Fantasy|Horror"),
    ("Twisters (2024)", "Action|Adventure|Thriller"),
    ("Despicable Me 4 (2024)", "Animation|Comedy"),
    ("Moana 2 (2024)", "Animation|Adventure|Comedy"),
    ("Wicked (2024)", "Fantasy|Musical|Drama"),
    ("Gladiator II (2024)", "Action|Adventure|Drama"),
    ("A Quiet Place: Day One (2024)", "Horror|Sci-Fi|Thriller"),
    ("The Wild Robot (2024)", "Animation|Adventure|Sci-Fi"),
    ("Joker: Folie a Deux (2024)", "Crime|Drama|Musical"),
    ("Venom: The Last Dance (2024)", "Action|Adventure|Sci-Fi"),
    ("It Ends with Us (2024)", "Drama|Romance"),
    ("Terrifier 3 (2024)", "Horror|Thriller"),
    ("Smile 2 (2024)", "Horror|Thriller"),
    ("Nosferatu (2024)", "Horror|Drama"),
    ("The Substance (2024)", "Horror|Sci-Fi|Drama"),
    ("Anora (2024)", "Comedy|Drama|Romance"),
    ("Conclave (2024)", "Drama|Thriller"),
    ("Emilia Perez (2024)", "Crime|Drama|Musical"),
    ("The Brutalist (2024)", "Drama"),
    ("Everything Everywhere All at Once (2022)", "Action|Adventure|Sci-Fi"),
    ("Top Gun: Maverick (2022)", "Action|Drama"),
    ("The Batman (2022)", "Action|Crime|Drama"),
    ("Avatar: The Way of Water (2022)", "Action|Adventure|Sci-Fi"),
    ("Black Panther: Wakanda Forever (2022)", "Action|Adventure|Drama"),
    ("Glass Onion: A Knives Out Mystery (2022)", "Comedy|Crime|Mystery"),
    ("The Banshees of Inisherin (2022)", "Comedy|Drama"),
    ("Tar (2022)", "Drama|Musical"),
    ("The Whale (2022)", "Drama"),
    ("Elvis (2022)", "Drama|Musical"),
    ("Nope (2022)", "Horror|Mystery|Sci-Fi"),
    ("Bullet Train (2022)", "Action|Comedy|Thriller"),
    ("Puss in Boots: The Last Wish (2022)", "Animation|Adventure|Comedy"),
    ("Marcel the Shell with Shoes On (2022)", "Animation|Comedy|Drama"),
    ("Turning Red (2022)", "Animation|Comedy|Fantasy"),
    ("Prey (2022)", "Action|Adventure|Thriller"),
    ("The Menu (2022)", "Comedy|Horror|Thriller"),
    ("Aftersun (2022)", "Drama"),
    ("Decision to Leave (2022)", "Mystery|Romance|Thriller"),
    ("RRR (2022)", "Action|Drama"),
    ("Parasite (2019)", "Comedy|Crime|Drama|Thriller"),
    ("Joker (2019)", "Crime|Drama|Thriller"),
    ("1917 (2019)", "Drama|War"),
    ("Knives Out (2019)", "Comedy|Crime|Mystery"),
    ("Ford v Ferrari (2019)", "Action|Drama"),
    ("Jojo Rabbit (2019)", "Comedy|Drama|War"),
    ("The Lighthouse (2019)", "Drama|Fantasy|Horror"),
    ("Uncut Gems (2019)", "Crime|Drama|Thriller"),
    ("Marriage Story (2019)", "Comedy|Drama|Romance"),
    ("Little Women (2019)", "Drama|Romance"),
    ("Spirited Away (2001)", "Animation|Adventure|Fantasy"),
    ("Princess Mononoke (1997)", "Animation|Adventure|Fantasy"),
    ("My Neighbor Totoro (1988)", "Animation|Comedy|Fantasy"),
    ("Howl's Moving Castle (2004)", "Animation|Adventure|Fantasy"),
    ("Grave of the Fireflies (1988)", "Animation|Drama|War"),
    ("Akira (1988)", "Animation|Action|Sci-Fi"),
    ("Ghost in the Shell (1995)", "Animation|Action|Sci-Fi"),
    ("Your Name (2016)", "Animation|Drama|Romance"),
    ("Weathering with You (2019)", "Animation|Drama|Romance|Fantasy"),
    ("A Silent Voice (2016)", "Animation|Drama"),
    ("Suzume (2022)", "Animation|Adventure|Fantasy"),
    ("The Wind Rises (2013)", "Animation|Drama|Romance"),
    ("Paprika (2006)", "Animation|Fantasy|Sci-Fi"),
    ("Wolf Children (2012)", "Animation|Drama|Fantasy"),
    ("Summer Wars (2009)", "Animation|Action|Comedy|Sci-Fi"),
    ("Demon Slayer: Mugen Train (2020)", "Animation|Action|Fantasy"),
    ("Jujutsu Kaisen 0 (2021)", "Animation|Action|Fantasy"),
    ("One Piece Film: Red (2022)", "Animation|Action|Adventure"),
    ("Dragon Ball Super: Broly (2018)", "Animation|Action|Adventure"),
    ("The First Slam Dunk (2022)", "Animation|Drama"),
]

# ══════════════════════════════════════════════════════════════
# 1.1 Admin Login
# ══════════════════════════════════════════════════════════════
section("1.1 Admin Login & JWT")

admin_token = None
admin_uid = None
try:
    # Try known admin accounts
    admin_creds = [
        ("admin@test.com", "admin123"),
        ("admin@test.com", "Admin123"),
        ("admin@test.com", "123456"),
        ("admin@test.com", "test123456"),
        ("nghiemlybaonu2004@gmail.com", "admin123"),
        ("nghiemlybaonu2004@gmail.com", "123456"),
    ]
    r = None
    for email, pwd in admin_creds:
        r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pwd})
        if r.status_code == 200:
            print(f"    Logged in with: {email}")
            break
    if r.status_code == 200:
        d = r.json()
        admin_token = d["access_token"]
        admin_uid = d["user_id"]
        TEST("Admin login OK", True, f"user_id={admin_uid}, role={d.get('role')}")
        TEST("JWT token received", len(admin_token) > 20, f"len={len(admin_token)}")
        TEST("Role is admin", d.get("role") == "admin")
    else:
        TEST("Admin login OK", False, f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    TEST("Admin login OK", False, str(e))

ADMIN_H = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

# ══════════════════════════════════════════════════════════════
# 1.2 RBAC Access Control
# ══════════════════════════════════════════════════════════════
section("1.2 RBAC Access Control")

# Admin can access /admin/stats
try:
    r = requests.get(f"{BASE}/admin/stats", headers=ADMIN_H)
    TEST("Admin GET /admin/stats => 200", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        stats = r.json()
        TEST("Stats has total_movies", "total_movies" in stats, str(stats))
except Exception as e:
    TEST("Admin GET /admin/stats", False, str(e))

# Admin can access /admin/users
try:
    r = requests.get(f"{BASE}/admin/users/", headers=ADMIN_H)
    TEST("Admin GET /admin/users => 200", r.status_code == 200, f"HTTP {r.status_code}")
except Exception as e:
    TEST("Admin GET /admin/users", False, str(e))

# No JWT => 401/403
try:
    r = requests.get(f"{BASE}/admin/stats")
    TEST("No JWT => /admin/stats blocked", r.status_code in (401, 403), f"HTTP {r.status_code}")
except Exception as e:
    TEST("No JWT test", False, str(e))

# Fake JWT => 401
try:
    r = requests.get(f"{BASE}/admin/stats", headers={"Authorization": "Bearer fake.token.here"})
    TEST("Fake JWT => blocked", r.status_code in (401, 403), f"HTTP {r.status_code}")
except Exception as e:
    TEST("Fake JWT test", False, str(e))

# Register a normal user for RBAC test
user_token = None
try:
    ts = int(time.time())
    test_email = f"rbac_test_{ts}@test.com"
    # Register
    requests.post(f"{BASE}/auth/register", json={"email": test_email, "password": "test123456"})
    # Force-verify in DB
    from src.database.db_config import DatabaseConnector
    conn = DatabaseConnector.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (test_email,))
    conn.commit()
    cur.close()
    conn.close()
    # Login
    r = requests.post(f"{BASE}/auth/login", json={"email": test_email, "password": "test123456"})
    if r.status_code == 200:
        user_token = r.json()["access_token"]
except:
    pass

if user_token:
    try:
        r = requests.get(f"{BASE}/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
        TEST("Normal user => /admin/stats => 403", r.status_code == 403, f"HTTP {r.status_code}")
    except Exception as e:
        TEST("Normal user RBAC", False, str(e))
else:
    TEST("Normal user RBAC", False, "Could not create test user")

# ══════════════════════════════════════════════════════════════
# 1.3 Bulk Insert 100 Movies
# ══════════════════════════════════════════════════════════════
section("1.3 Bulk Insert 100 Movies")

inserted_ids = []
failed_count = 0

if admin_token:
    for i, (title, genres) in enumerate(MOVIES_SEED):
        try:
            r = requests.post(
                f"{BASE}/admin/movies/",
                headers=ADMIN_H,
                json={"title": title, "genres_str": genres},
            )
            if r.status_code == 201:
                mid = r.json().get("movie_id")
                inserted_ids.append(mid)
            else:
                failed_count += 1
        except:
            failed_count += 1

        if (i + 1) % 25 == 0:
            print(f"    ... {i+1}/100 movies inserted")

    TEST("100 movies inserted", len(inserted_ids) >= 95,
         f"OK={len(inserted_ids)}, FAIL={failed_count}")
    TEST("All movie_ids > 3883", all(mid > 3883 for mid in inserted_ids) if inserted_ids else False)

    # Verify in DB
    try:
        r = requests.get(f"{BASE}/admin/stats", headers=ADMIN_H)
        if r.status_code == 200:
            total = r.json()["total_movies"]
            TEST("DB movie count increased", total >= 3883 + len(inserted_ids),
                 f"total_movies={total}")
    except:
        pass
else:
    TEST("Bulk insert skipped", False, "No admin token")

# Save results for later
import json as _json
out_path = Path(__file__).parent / "phase1_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    _json.dump({
        "results": results,
        "inserted_movie_ids": inserted_ids,
        "admin_token": admin_token,
        "admin_uid": admin_uid,
    }, f, ensure_ascii=False, indent=2)

# Summary
section("PHASE 1 SUMMARY")
p = sum(1 for r in results if r["status"] == "PASS")
f_ = sum(1 for r in results if r["status"] == "FAIL")
print(f"  PASSED: {p}/{len(results)}  |  FAILED: {f_}")
print(f"  Movies inserted: {len(inserted_ids)}")
print(f"  Results saved: {out_path}")
