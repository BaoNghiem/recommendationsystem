"""
Phase 3: Legacy Users + Ratings Seed + Model Retraining
=======================================================
"""
import sys, os, time, json, random, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

results = []

def TEST(name, passed, detail=""):
    s = "PASS" if passed else "FAIL"
    results.append({"test": name, "status": s, "detail": detail, "phase": 3})
    print(f"  [{'OK' if passed else 'XX'}] {name}" + (f" | {detail}" if detail else ""))

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# Load phase1 data
p1_path = Path(__file__).parent / "phase1_results.json"
p1 = json.loads(p1_path.read_text(encoding="utf-8")) if p1_path.exists() else {}
inserted_ids = p1.get("inserted_movie_ids", [])

from src.database.db_config import DatabaseConnector

# ══════════════════════════════════════════════════════════════
# 3.1 Create 10 Legacy Test Users + 200-300 Ratings
# ══════════════════════════════════════════════════════════════
section("3.1 Create 10 Legacy Test Users")

legacy_uids = []
conn = DatabaseConnector.get_connection()
cur = conn.cursor()

try:
    # Get next available user_id in legacy range (use 6901-6910)
    cur.execute("SELECT MAX(user_id) FROM users WHERE user_id < 7001")
    max_legacy = cur.fetchone()[0] or 6040
    base_id = max_legacy + 1

    genders = ["M", "F"]
    ages = [18, 25, 35, 45, 50]
    occupations = list(range(0, 20))

    for i in range(10):
        uid = base_id + i
        g = random.choice(genders)
        age = random.choice(ages)
        occ = random.choice(occupations)
        email = f"legacy_test_{uid}@moviedb.local"

        try:
            cur.execute("""
                INSERT INTO users (user_id, gender, age, occupation, zip_code,
                                   email, password_hash, role, account_type,
                                   is_active, email_verified)
                VALUES (%s, %s, %s, %s, '00000', %s, 'LEGACY_ACCOUNT_NO_LOGIN',
                        'user', 'legacy', TRUE, TRUE)
                ON CONFLICT (user_id) DO NOTHING
            """, (uid, g, age, occ, email))
            legacy_uids.append(uid)
        except Exception as e:
            print(f"    Skip user {uid}: {e}")

    conn.commit()
    TEST(f"Created {len(legacy_uids)} legacy users", len(legacy_uids) == 10,
         f"IDs: {legacy_uids}")
except Exception as e:
    conn.rollback()
    TEST("Create legacy users", False, str(e))

# ══════════════════════════════════════════════════════════════
# 3.2 Insert 200-300 Random Ratings
# ══════════════════════════════════════════════════════════════
section("3.2 Insert 200-300 Random Ratings")

total_ratings = 0
rating_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

# Get all movie_ids (seeded + existing)
cur.execute("SELECT movie_id FROM movies")
all_movie_ids = [r[0] for r in cur.fetchall()]

# Record pre-train state
cur.execute("SELECT COUNT(*) FROM ratings")
pre_train_ratings = cur.fetchone()[0]

target_ratings = random.randint(200, 300)
ratings_per_user = target_ratings // len(legacy_uids) if legacy_uids else 0

try:
    for uid in legacy_uids:
        # Each user rates ~20-30 random movies
        sample_size = min(ratings_per_user + random.randint(-3, 3), len(all_movie_ids))
        movies_sample = random.sample(all_movie_ids, sample_size)

        for mid in movies_sample:
            rating = random.choice(rating_values)
            ts = int(time.time()) - random.randint(0, 86400 * 365)
            try:
                cur.execute("""
                    INSERT INTO ratings (user_id, movie_id, rating, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, movie_id) DO UPDATE
                    SET rating = EXCLUDED.rating, timestamp = EXCLUDED.timestamp
                """, (uid, mid, rating, ts))
                total_ratings += 1
            except:
                pass

    conn.commit()
    TEST(f"Inserted {total_ratings} ratings", 200 <= total_ratings <= 400,
         f"target={target_ratings}, actual={total_ratings}")
except Exception as e:
    conn.rollback()
    TEST("Insert ratings", False, str(e))

cur.execute("SELECT COUNT(*) FROM ratings")
post_seed_ratings = cur.fetchone()[0]
TEST("Ratings count increased", post_seed_ratings > pre_train_ratings,
     f"before={pre_train_ratings}, after={post_seed_ratings}")

cur.close()
conn.close()

# ══════════════════════════════════════════════════════════════
# 3.3 Run Model Retraining
# ══════════════════════════════════════════════════════════════
section("3.3 Model Retraining (main_train.py)")

BASE_DIR = Path(__file__).resolve().parent.parent
train_script = BASE_DIR / "main_train.py"
model_path = BASE_DIR / "output" / "models" / "funksvd_model.pkl"

# Record pre-train model timestamp
pre_train_mtime = model_path.stat().st_mtime if model_path.exists() else 0

print(f"  Running: python {train_script}")
print(f"  This may take 1-3 minutes...")

try:
    proc = subprocess.run(
        [sys.executable, str(train_script)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8",
        errors="replace",
    )

    TEST("main_train.py exit code = 0", proc.returncode == 0,
         f"returncode={proc.returncode}")

    # Check for charmap errors
    has_charmap = "charmap" in proc.stderr.lower() if proc.stderr else False
    TEST("No charmap encoding errors", not has_charmap,
         "stderr clean" if not has_charmap else proc.stderr[:200])

    # Check model file updated
    post_train_mtime = model_path.stat().st_mtime if model_path.exists() else 0
    TEST("Model file updated", post_train_mtime > pre_train_mtime,
         f"before={pre_train_mtime:.0f}, after={post_train_mtime:.0f}")

    # Parse training output for metrics
    stdout = proc.stdout or ""
    if "RMSE" in stdout:
        for line in stdout.split("\n"):
            if "RMSE" in line:
                print(f"    {line.strip()}")
            if "MAE" in line:
                print(f"    {line.strip()}")
            if "NDCG" in line:
                print(f"    {line.strip()}")

    TEST("Training output contains RMSE", "RMSE" in stdout)
    TEST("Training output contains NDCG", "NDCG" in stdout)

except subprocess.TimeoutExpired:
    TEST("Training timeout", False, "Exceeded 300s")
except Exception as e:
    TEST("Training execution", False, str(e))

# ══════════════════════════════════════════════════════════════
# 3.4 Regression Test (run existing test suite)
# ══════════════════════════════════════════════════════════════
section("3.4 Regression Test (test_ai_engine.py)")

test_script = Path(__file__).parent / "test_ai_engine.py"
if test_script.exists():
    try:
        proc = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        stdout = proc.stdout or ""
        has_charmap = "charmap" in (proc.stderr or "").lower()
        TEST("Regression: no charmap errors", not has_charmap)

        # Count PASS/FAIL in output
        pass_count = stdout.count("[PASS]")
        fail_count = stdout.count("[FAIL]")
        TEST(f"Regression: {pass_count} PASS, {fail_count} FAIL",
             fail_count == 0 and pass_count > 0,
             f"PASS={pass_count}, FAIL={fail_count}")

    except Exception as e:
        TEST("Regression test", False, str(e))
else:
    TEST("Regression test", False, "test_ai_engine.py not found")

# Save results
out_path = Path(__file__).parent / "phase3_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "results": results,
        "legacy_uids": legacy_uids,
        "total_ratings_inserted": total_ratings,
        "pre_train_ratings": pre_train_ratings,
        "post_seed_ratings": post_seed_ratings,
    }, f, ensure_ascii=False, indent=2)

section("PHASE 3 SUMMARY")
p = sum(1 for r in results if r["status"] == "PASS")
f_ = sum(1 for r in results if r["status"] == "FAIL")
print(f"  PASSED: {p}/{len(results)}  |  FAILED: {f_}")
print(f"  Legacy users: {legacy_uids}")
print(f"  Ratings inserted: {total_ratings}")
