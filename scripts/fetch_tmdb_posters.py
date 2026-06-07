"""
scripts/fetch_tmdb_posters.py
==============================
Tự động lấy poster phim từ TMDB API và lưu vào DB.

Bước 1: Lấy API key miễn phí tại https://www.themoviedb.org/settings/api
Bước 2: Thêm vào .env:  TMDB_API_KEY=your_key_here
Bước 3: Chạy: python scripts/fetch_tmdb_posters.py

Script sẽ:
- Tìm kiếm tên phim trên TMDB
- Lưu poster_url vào DB (chỉ cập nhật phim chưa có poster)
- Lưu URL dạng: https://image.tmdb.org/t/p/w500/... (không download về local)
- Bỏ qua phim đã có poster
"""
import sys, os, time, re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
if sys.platform.startswith('win'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH   = "https://api.themoviedb.org/3/search/movie"

def clean_title(raw: str) -> tuple[str, str | None]:
    """Bỏ năm và sắp xếp lại mạo từ: 'Godfather, The (1972)' → ('The Godfather', '1972')"""
    year_match = re.search(r'\((\d{4})\)', raw)
    year = year_match.group(1) if year_match else None
    title = re.sub(r'\s*\(\d{4}\)', '', raw).strip()
    # Đảo mạo từ: "Godfather, The" → "The Godfather"
    article_match = re.match(r'^(.+),\s*(The|A|An)$', title, re.IGNORECASE)
    if article_match:
        title = f"{article_match.group(2)} {article_match.group(1).strip()}"
    return title, year


def search_tmdb(title: str, year: str | None, api_key: str) -> str | None:
    """Tìm poster trên TMDB. Trả về URL hoặc None."""
    import urllib.request, json, urllib.parse
    params = {"api_key": api_key, "query": title, "language": "en-US", "page": 1}
    if year:
        params["year"] = year
    url = TMDB_SEARCH + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        if results and results[0].get("poster_path"):
            return TMDB_IMG_BASE + results[0]["poster_path"]
        # Thử lại không có year filter
        if year:
            return search_tmdb(title, None, api_key)
    except Exception as e:
        pass
    return None


def main():
    if not TMDB_API_KEY:
        print("[ERROR] TMDB_API_KEY chua duoc thiet lap trong .env")
        print("        1. Dang ky tai: https://www.themoviedb.org/settings/api")
        print("        2. Them vao .env: TMDB_API_KEY=your_key_here")
        sys.exit(1)

    from src.database.db_config import DatabaseConnector
    conn = DatabaseConnector.get_connection()
    cur = conn.cursor()

    # Lay phim chua co poster
    cur.execute("""
        SELECT movie_id, title FROM movies
        WHERE poster_url IS NULL OR poster_url = ''
        ORDER BY movie_id
    """)
    movies = cur.fetchall()
    total = len(movies)
    print(f"[FETCH] Can lay poster cho {total} phim...")
    print(f"[FETCH] TMDB API Key: {TMDB_API_KEY[:8]}***")
    print()

    updated = 0
    failed = 0

    for i, (movie_id, raw_title) in enumerate(movies):
        title, year = clean_title(raw_title)
        poster_url = search_tmdb(title, year, TMDB_API_KEY)

        if poster_url:
            cur.execute(
                "UPDATE movies SET poster_url = %s WHERE movie_id = %s",
                (poster_url, movie_id)
            )
            updated += 1
            if updated % 50 == 0:
                conn.commit()  # commit theo batch 50
                print(f"  [{i+1}/{total}] Updated {updated} posters...")
        else:
            failed += 1

        # Rate limit: TMDB cho phep 40 requests/10s
        if (i + 1) % 40 == 0:
            time.sleep(0.5)

    conn.commit()
    cur.close()
    conn.close()

    print()
    print(f"[DONE] Cap nhat thanh cong: {updated}/{total} phim")
    print(f"       Khong tim thay:      {failed} phim")
    print()
    print("[NEXT] Restart backend de AP clear cache:")
    print("       uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload")


if __name__ == "__main__":
    main()
