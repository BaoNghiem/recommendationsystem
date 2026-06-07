"""
enrich_movies.py — Làm giàu metadata phim qua OMDB API
=======================================================
Điền các trường: country, description, total_episodes cho tất cả phim trong DB.

Cách dùng:
  1. Lấy API key miễn phí tại: https://www.omdbapi.com/apikey.aspx
  2. Đặt vào biến OMDB_API_KEY bên dưới (hoặc file .env)
  3. python scripts/enrich_movies.py

Lưu ý:
  - Free tier: 1000 requests/ngày.
  - MovieLens 1M có 3883 phim → cần ~4 ngày nếu dùng miễn phí.
  - Script có thể resume (bỏ qua phim đã có description).
  - Dùng --limit N để test trước khi chạy toàn bộ.
"""
import sys
import time
import re
import argparse
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db_config import DatabaseConnector

# ── Cấu hình ──────────────────────────────────────────────────
OMDB_API_KEY = "YOUR_OMDB_API_KEY"   # Thay bằng key thật
OMDB_BASE    = "http://www.omdbapi.com/"
DELAY_SEC    = 0.2   # Delay giữa mỗi request (tránh rate-limit)

# Mapping tên quốc gia OMDB → tên chuẩn ngắn gọn hơn
COUNTRY_NORMALIZE = {
    "USA": "Mỹ",
    "UK": "Anh",
    "France": "Pháp",
    "Germany": "Đức",
    "Italy": "Ý",
    "Japan": "Nhật Bản",
    "South Korea": "Hàn Quốc",
    "India": "Ấn Độ",
    "Australia": "Úc",
    "Canada": "Canada",
    "Spain": "Tây Ban Nha",
    "Sweden": "Thụy Điển",
    "Denmark": "Đan Mạch",
    "Ireland": "Ireland",
    "Hong Kong": "Hồng Kông",
    "China": "Trung Quốc",
}


def normalize_country(raw: str) -> str:
    """Lấy quốc gia đầu tiên từ chuỗi 'USA, UK, France'."""
    if not raw or raw == "N/A":
        return None
    first = raw.split(",")[0].strip()
    return COUNTRY_NORMALIZE.get(first, first)


def clean_title_for_search(title: str) -> str:
    """Chuan hoa title MovieLens truoc khi tim kiem OMDB.
       - 'Toy Story (1995)'      -> 'Toy Story'
       - 'Godfather, The (1972)' -> 'The Godfather'
       - "Bug's Life, A (1998)"  -> "A Bug's Life"
    """
    # Loai bo nam
    clean = re.sub(r'\s*\(\d{4}\)\s*$', '', title).strip()
    # Chuyen 'Name, The' -> 'The Name'
    match = re.match(r'^(.+),\s*(The|A|An)\s*$', clean, re.IGNORECASE)
    if match:
        clean = f"{match.group(2)} {match.group(1).strip()}"
    return clean


def extract_year_from_title(title: str) -> str | None:
    """Trích xuất năm từ title: 'Toy Story (1995)' → '1995'."""
    m = re.search(r'\((\d{4})\)\s*$', title)
    return m.group(1) if m else None


def fetch_omdb(title: str, year: str | None) -> dict | None:
    """Gọi OMDB API, trả về dict JSON hoặc None nếu lỗi."""
    params = {
        "apikey": OMDB_API_KEY,
        "t": clean_title_for_search(title),
        "plot": "short",
    }
    if year:
        params["y"] = year

    try:
        resp = requests.get(OMDB_BASE, params=params, timeout=10)
        data = resp.json()
        if data.get("Response") == "True":
            return data
        # Thử lại không có năm nếu thất bại
        if year:
            params.pop("y", None)
            resp2 = requests.get(OMDB_BASE, params=params, timeout=10)
            data2 = resp2.json()
            if data2.get("Response") == "True":
                return data2
    except Exception as e:
        print(f"  [OMDB ERROR] {title}: {e}")
    return None


def parse_episodes(data: dict) -> int | None:
    """Tổng số tập từ OMDB (chỉ có cho TV Series)."""
    if data.get("Type") != "series":
        return None
    # OMDB trả totalSeasons, không trả tổng tập trực tiếp
    # Ta dùng totalSeasons * 10 làm ước tính, hoặc để NULL
    seasons = data.get("totalSeasons", "N/A")
    if seasons and seasons != "N/A":
        try:
            return int(seasons) * 10  # ước tính trung bình 10 tập/mùa
        except ValueError:
            pass
    return None

def enrich(limit: int = None, dry_run: bool = False, force: bool = False):
    """Chay enrichment cho phim chua co description hoac co placeholder."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        print("[ERROR] Khong the ket noi database.")
        return

    cur = conn.cursor()

    # Lay danh sach phim chua duoc enrich
    # Bao gom ca phim co placeholder '(Chua co mo ta)' de thu lai
    cur.execute("""
        SELECT movie_id, title
        FROM movies
        WHERE description IS NULL
           OR description = '(Chua co mo ta)'
        ORDER BY movie_id
        LIMIT %s
    """, (limit if limit else 999999,))
    movies = cur.fetchall()
    print(f"[ENRICH] Can xu ly: {len(movies)} phim\n")

    success = 0
    not_found = 0

    for i, (movie_id, title) in enumerate(movies, 1):
        year = extract_year_from_title(title)
        print(f"[{i}/{len(movies)}] #{movie_id} — {title}", end=" ... ")

        data = fetch_omdb(title, year)

        if not data:
            print("\u274c Khong tim thay")
            not_found += 1
            # Set default values de khong query lai lan sau
            if not dry_run:
                cur.execute("""
                    UPDATE movies
                    SET country = COALESCE(country, %s),
                        description = COALESCE(description, %s)
                    WHERE movie_id = %s
                """, ("M\u1ef9", "(Ch\u01b0a c\u00f3 m\u00f4 t\u1ea3)", movie_id))
                conn.commit()
            time.sleep(DELAY_SEC)
            continue

        country     = normalize_country(data.get("Country", ""))
        description = data.get("Plot", "")
        episodes    = parse_episodes(data)

        if description == "N/A":
            description = None

        print(f"✅ {country or '?'} | {data.get('Type','?')}")

        if not dry_run:
            cur.execute("""
                UPDATE movies
                SET country = COALESCE(%s, country),
                    description = COALESCE(%s, description),
                    total_episodes = COALESCE(%s, total_episodes)
                WHERE movie_id = %s
            """, (country, description, episodes, movie_id))
            conn.commit()

        success += 1
        time.sleep(DELAY_SEC)

    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"[DONE] Thành công: {success} | Không tìm thấy: {not_found}")
    print(f"       Phim không tìm thấy đã được đặt mặc định country='Mỹ'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich movie metadata from OMDB API")
    parser.add_argument("--limit", type=int, default=None,
                        help="Gioi han so phim xu ly (mac dinh: tat ca)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chay thu, khong ghi vao DB")
    parser.add_argument("--force", action="store_true",
                        help="Xu ly lai ca phim co placeholder description")
    args = parser.parse_args()

    if OMDB_API_KEY == "YOUR_OMDB_API_KEY":
        print("[ERROR] Chua dat OMDB_API_KEY!")
        print("        Lay key mien phi tai: https://www.omdbapi.com/apikey.aspx")
        sys.exit(1)

    enrich(limit=args.limit, dry_run=args.dry_run, force=args.force)
