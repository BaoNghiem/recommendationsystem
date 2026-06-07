"""
Phase 4: Post-Retrain Quality Audit (Diversity, Novelty, Strategy Validation)
=============================================================================
"""
import sys, os, time, json, requests
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE = "http://127.0.0.1:8000"
results = []

def TEST(name, passed, detail=""):
    s = "PASS" if passed else "FAIL"
    results.append({"test": name, "status": s, "detail": detail, "phase": 4})
    print(f"  [{'OK' if passed else 'XX'}] {name}" + (f" | {detail}" if detail else ""))

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# Load previous phase data
p1 = json.loads((Path(__file__).parent / "phase1_results.json").read_text(encoding="utf-8"))
p2 = json.loads((Path(__file__).parent / "phase2_results.json").read_text(encoding="utf-8"))
p3 = json.loads((Path(__file__).parent / "phase3_results.json").read_text(encoding="utf-8"))

admin_token = p1.get("admin_token")
cold_uid = p2.get("cold_uid")
cold_token = p2.get("cold_token")   # BUG B FIX: Load token tu phase2
legacy_uids = p3.get("legacy_uids", [])
inserted_ids = p1.get("inserted_movie_ids", [])
inserted_set = set(inserted_ids)

ADMIN_H = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
COLD_H  = {"Authorization": f"Bearer {cold_token}"} if cold_token else {}

# ══════════════════════════════════════════════════════════════
# 4.1 Verify Cold User Strategy Post-Retrain
# ══════════════════════════════════════════════════════════════
section("4.1 Cold User Recommendations (Post-Retrain)")

if cold_uid and cold_token:
    # BUG B FIX: Dung cold_token (luu tu phase2) de pass JWT + IDOR guard
    r = requests.get(f"{BASE}/recommend/{cold_uid}", headers=COLD_H)
    if r.status_code == 200:
        data = r.json()
        strategy = data.get("strategy", "")
        recs = data.get("recommendations", [])

        TEST("Cold user gets recs post-retrain", len(recs) > 0, f"{len(recs)} movies")
        TEST("Strategy after retrain",
             strategy in ("hybrid_foldin", "content_based", "hybrid"),
             f"strategy='{strategy}'")

        print(f"\n  Strategy: {strategy}")
        print(f"  Explanation: {data.get('explanation', '')}")
    else:
        TEST("Cold user recs", False, f"HTTP {r.status_code}: {r.text[:100]}")
else:
    TEST("Cold user test skipped", False, "No cold_uid or cold_token — re-run Phase 2 first")

# ══════════════════════════════════════════════════════════════
# 4.2 Legacy Users Recommendations - FunkSVD Pure
# ══════════════════════════════════════════════════════════════
section("4.2 Legacy Users - FunkSVD Strategy Validation")

# BUG B FIX: Legacy users khong the login (bi block), nen tao JWT truc tiep
# de test recommendation endpoint voi dung auth header.
try:
    from src.api.auth.utils import create_access_token
    def make_user_token(uid: int) -> str:
        return create_access_token({"sub": str(uid), "role": "user"})
except Exception:
    make_user_token = None

strategy_counts = Counter()
all_recs_data = {}

for uid in legacy_uids[:5]:  # Test 5 of 10
    try:
        if make_user_token is None:
            TEST(f"User {uid} recs", False, "Cannot create token")
            continue
        user_token = make_user_token(uid)
        user_h = {"Authorization": f"Bearer {user_token}"}
        r = requests.get(f"{BASE}/recommend/{uid}", headers=user_h)
        if r.status_code == 200:
            data = r.json()
            s = data.get("strategy", "unknown")
            strategy_counts[s] += 1
            all_recs_data[uid] = data

            recs = data.get("recommendations", [])
            TEST(f"User {uid}: {len(recs)} recs via '{s}'",
                 len(recs) > 0 and s in ("hybrid", "hybrid_foldin"),
                 f"strategy={s}")
    except Exception as e:
        TEST(f"User {uid} recs", False, str(e))

TEST("Majority use hybrid/SVD strategy",
     strategy_counts.get("hybrid", 0) + strategy_counts.get("hybrid_foldin", 0) >= 3,
     f"strategies={dict(strategy_counts)}")

# ══════════════════════════════════════════════════════════════
# 4.3 Diversity Audit
# ══════════════════════════════════════════════════════════════
section("4.3 Diversity Audit")

for uid, data in list(all_recs_data.items())[:3]:
    recs = data.get("recommendations", [])
    if not recs:
        continue

    # Extract all genres
    all_genres = []
    for rec in recs[:20]:
        genres = rec.get("genres_orig", "")
        for g in genres.split("|"):
            g = g.strip()
            if g:
                all_genres.append(g)

    genre_counter = Counter(all_genres)
    unique_genres = len(genre_counter)
    total_genre_tags = len(all_genres)

    # Diversity = unique genres / total possible (18)
    diversity = unique_genres / 18.0
    TEST(f"User {uid}: Diversity = {diversity:.1%}",
         unique_genres >= 4,
         f"{unique_genres} unique genres in top-20")

    # Top genres
    top3 = genre_counter.most_common(3)
    print(f"    Top genres: {', '.join(f'{g}({c})' for g, c in top3)}")

# ══════════════════════════════════════════════════════════════
# 4.4 Novelty Audit (New movies in recommendations)
# ══════════════════════════════════════════════════════════════
section("4.4 Novelty Audit (New Movies)")

for uid, data in list(all_recs_data.items())[:3]:
    recs = data.get("recommendations", [])
    if not recs:
        continue

    rec_ids = [r["movie_id"] for r in recs[:20]]
    new_movie_count = sum(1 for mid in rec_ids if mid in inserted_set)
    novelty_pct = (new_movie_count / len(rec_ids)) * 100 if rec_ids else 0

    TEST(f"User {uid}: {new_movie_count} new movies in top-20",
         True,  # Just report, not fail
         f"novelty={novelty_pct:.1f}%")

    if new_movie_count > 0:
        new_titles = [r["title"] for r in recs[:20] if r["movie_id"] in inserted_set]
        for t in new_titles[:3]:
            print(f"    NEW: {t}")

# ══════════════════════════════════════════════════════════════
# 4.5 Cross-User Recommendation Uniqueness
# ══════════════════════════════════════════════════════════════
section("4.5 Personalization Check (Cross-User Uniqueness)")

if len(all_recs_data) >= 2:
    uids = list(all_recs_data.keys())
    rec_sets = {}
    for uid in uids[:3]:
        recs = all_recs_data[uid].get("recommendations", [])
        rec_sets[uid] = set(r["movie_id"] for r in recs[:10])

    pairs = [(uids[i], uids[j]) for i in range(len(uids[:3])) for j in range(i+1, len(uids[:3]))]
    for u1, u2 in pairs:
        s1, s2 = rec_sets.get(u1, set()), rec_sets.get(u2, set())
        if s1 and s2:
            overlap = len(s1 & s2)
            jaccard = overlap / len(s1 | s2) if (s1 | s2) else 0
            TEST(f"Users {u1} vs {u2}: Jaccard={jaccard:.2f}",
                 jaccard < 0.8,
                 f"overlap={overlap}/10, personalized={'Yes' if jaccard < 0.5 else 'Partial'}")

# ══════════════════════════════════════════════════════════════
# 4.6 System Stats After All Tests
# ══════════════════════════════════════════════════════════════
section("4.6 Final System Stats")

if admin_token:
    r = requests.get(f"{BASE}/admin/stats", headers=ADMIN_H)
    if r.status_code == 200:
        stats = r.json()
        print(f"  Total Movies:  {stats.get('total_movies')}")
        print(f"  Total Ratings: {stats.get('total_ratings')}")
        print(f"  Total Users:   {stats.get('total_users')}")
        print(f"  Real Users:    {stats.get('real_users')}")
        TEST("Final stats retrieved", True, json.dumps(stats))

# Save results
out_path = Path(__file__).parent / "phase4_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "results": results,
        "strategy_counts": dict(strategy_counts),
    }, f, ensure_ascii=False, indent=2)

section("PHASE 4 SUMMARY")
p = sum(1 for r in results if r["status"] == "PASS")
f_ = sum(1 for r in results if r["status"] == "FAIL")
print(f"  PASSED: {p}/{len(results)}  |  FAILED: {f_}")
