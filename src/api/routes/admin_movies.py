"""
Admin Movie CRUD Routes: /admin/movies
- GET    /admin/movies          — Danh sách phim + pagination + search
- GET    /admin/movies/{id}     — Chi tiết 1 phim (kèm metadata + stats)
- POST   /admin/movies          — Thêm phim mới (ghi movies + movie_genres)
- PUT    /admin/movies/{id}     — Sửa phim (cập nhật cả hai bảng)
- DELETE /admin/movies/{id}     — Xóa phim (cascade xóa movie_genres + ratings)
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import uuid
from pathlib import Path
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import require_admin

router = APIRouter(prefix="/admin/movies", tags=["Admin - Movies"])

# ── Genre mapping: tên hiển thị → tên cột DB ──────────────────
GENRE_MAP = {
    "Action":      "action",
    "Adventure":   "adventure",
    "Animation":   "animation",
    "Children's":  "childrens",
    "Comedy":      "comedy",
    "Crime":       "crime",
    "Documentary": "documentary",
    "Drama":       "drama",
    "Fantasy":     "fantasy",
    "Film-Noir":   "film_noir",
    "Horror":      "horror",
    "Musical":     "musical",
    "Mystery":     "mystery",
    "Romance":     "romance",
    "Sci-Fi":      "sci_fi",
    "Thriller":    "thriller",
    "War":         "war",
    "Western":     "western",
}
ALL_GENRE_COLS = list(GENRE_MAP.values())


def encode_genres(genres_str: str) -> dict:
    """
    Chuyển chuỗi 'Action|Comedy|Drama' thành dict {col: 0/1}.
    Ví dụ: {'action':1, 'comedy':1, 'drama':1, 'thriller':0, ...}
    """
    parts = {g.strip() for g in genres_str.split("|") if g.strip()}
    result = {col: 0 for col in ALL_GENRE_COLS}
    for display_name, col_name in GENRE_MAP.items():
        if display_name in parts:
            result[col_name] = 1
    return result


def next_movie_id(cur) -> int:
    """Lấy ID tiếp theo cho phim mới (MAX hiện tại + 1, tối thiểu 3884)."""
    cur.execute("SELECT MAX(movie_id) FROM movies")
    max_id = cur.fetchone()[0] or 3883
    return max(max_id + 1, 3884)


# ── Pydantic schemas ────────────────────────────────────────────
class MovieCreate(BaseModel):
    title:          str
    genres_str:     str             # Ví dụ: "Action|Comedy"
    release_year:   Optional[int]   = None
    country:        Optional[str]   = None
    total_episodes: Optional[int]   = None
    description:    Optional[str]   = None
    poster_url:     Optional[str]   = None


class MovieUpdate(BaseModel):
    title:          Optional[str]   = None
    genres_str:     Optional[str]   = None
    release_year:   Optional[int]   = None
    country:        Optional[str]   = None
    total_episodes: Optional[int]   = None
    description:    Optional[str]   = None
    poster_url:     Optional[str]   = None


# ── GET /admin/movies/ ─────────────────────────────────────────
@router.get("/")
async def list_movies(
    page:  int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q:     str = Query("", description="Tìm theo tên phim"),
    admin: dict = Depends(require_admin),
):
    """Danh sách phim có phân trang và tìm kiếm, kèm metadata mới."""
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        base_select = """
            SELECT movie_id, title, genres_orig,
                   release_year, country, total_episodes, description, poster_url
            FROM movies
        """
        if q:
            pattern = f"%{q}%"
            cur.execute("SELECT COUNT(*) FROM movies WHERE title ILIKE %s", (pattern,))
            total = cur.fetchone()[0]
            cur.execute(
                base_select + "WHERE title ILIKE %s ORDER BY movie_id DESC LIMIT %s OFFSET %s",
                (pattern, limit, offset),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM movies")
            total = cur.fetchone()[0]
            cur.execute(
                base_select + "ORDER BY movie_id DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )

        rows = cur.fetchall()
        movies = [
            {
                "movie_id":       r[0],
                "title":          r[1],
                "genres_orig":    r[2],
                "release_year":   r[3],
                "country":        r[4],
                "total_episodes": r[5],
                "description":    r[6],
                "poster_url":     r[7],
            }
            for r in rows
        ]
        return {
            "movies":      movies,
            "total":       total,
            "page":        page,
            "limit":       limit,
            "total_pages": (total + limit - 1) // limit,
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


# ── GET /admin/movies/{movie_id} ───────────────────────────────
@router.get("/{movie_id}")
async def get_movie(movie_id: int, admin: dict = Depends(require_admin)):
    """Chi tiết phim kèm avg_rating, vote_count, và toàn bộ metadata."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.movie_id, m.title, m.genres_orig,
                   m.release_year, m.country, m.total_episodes, m.description, m.poster_url,
                   COALESCE(ROUND(AVG(r.rating)::numeric, 2), NULL) AS avg_rating,
                   COUNT(r.rating) AS vote_count
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE m.movie_id = %s
            GROUP BY m.movie_id, m.title, m.genres_orig,
                     m.release_year, m.country, m.total_episodes, m.description, m.poster_url
        """, (movie_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")
        return {
            "movie_id":       row[0],
            "title":          row[1],
            "genres_orig":    row[2],
            "release_year":   row[3],
            "country":        row[4],
            "total_episodes": row[5],
            "description":    row[6],
            "poster_url":     row[7],
            "avg_rating":     float(row[8]) if row[8] is not None else None,
            "vote_count":     row[9],
        }
    finally:
        cur.close()
        conn.close()


# ── POST /admin/movies/ ────────────────────────────────────────
@router.post("/", status_code=201)
async def create_movie(body: MovieCreate, admin: dict = Depends(require_admin)):
    """
    Thêm phim mới. Backend tự động:
    - Gán movie_id tiếp theo (MAX + 1)
    - Ghi metadata vào bảng movies
    - Encode genres_str và ghi vào bảng movie_genres (tách biệt)
    """
    if not body.title or not body.title.strip():
        raise HTTPException(400, "Tiêu đề phim không được để trống.")
    if not body.genres_str or not body.genres_str.strip():
        raise HTTPException(400, "Thể loại phim không được để trống.")

    genres_encoded = encode_genres(body.genres_str)
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        new_id = next_movie_id(cur)

        # 1. Ghi vào bảng movies (metadata)
        cur.execute("""
            INSERT INTO movies (movie_id, title, genres_orig, release_year, country, total_episodes, description, poster_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING movie_id
        """, (
            new_id,
            body.title.strip(),
            body.genres_str.strip(),
            body.release_year,
            body.country,
            body.total_episodes,
            body.description,
            body.poster_url,   # BUG #1 FIX: poster_url được lưu ngay khi tạo phim
        ))
        inserted_id = cur.fetchone()[0]

        # 2. Ghi vào bảng movie_genres (18 cột binary cho AI + Filter)
        genre_cols = ", ".join(ALL_GENRE_COLS)
        genre_vals = ", ".join(["%s"] * len(ALL_GENRE_COLS))
        genre_values = [genres_encoded[c] for c in ALL_GENRE_COLS]

        cur.execute(
            f"INSERT INTO movie_genres (movie_id, {genre_cols}) VALUES (%s, {genre_vals})",
            [inserted_id] + genre_values,
        )

        conn.commit()
        print(f"[ADMIN] Created movie: ID={inserted_id}, Title='{body.title}'")
        return {
            "message":  "Thêm phim thành công.",
            "movie_id": inserted_id,
            "title":    body.title,
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lỗi thêm phim: {e}")
    finally:
        cur.close()
        conn.close()


# ── PUT /admin/movies/{movie_id} ───────────────────────────────
@router.put("/{movie_id}")
async def update_movie(
    movie_id: int,
    body: MovieUpdate,
    admin: dict = Depends(require_admin),
):
    """
    Sửa phim. Cập nhật đồng thời:
    - Bảng movies: title, genres_orig, release_year, country, total_episodes, description
    - Bảng movie_genres: 18 cột 0/1 (khi genres_str thay đổi)
    """
    # BUG FIX: Dung `is not None` cho tat ca truong — tranh coi chuoi rong ('') la "khong co update"
    # Vi du: body.country='' (xoa country) phai duoc coi la cap nhat hop le
    has_update = any([
        body.title is not None, body.genres_str is not None,
        body.release_year is not None, body.country is not None,
        body.total_episodes is not None, body.description is not None,
        body.poster_url is not None,
    ])
    if not has_update:
        raise HTTPException(400, "Cần ít nhất một trường để cập nhật.")

    if body.title is not None and not body.title.strip():
        raise HTTPException(400, "Tiêu đề phim không được để trống.")
    if body.genres_str is not None and not body.genres_str.strip():
        raise HTTPException(400, "Thể loại phim không được để trống.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")

        # ── Cập nhật bảng movies ──────────────────────────────
        movie_sets, movie_params = [], []

        if body.title:
            movie_sets.append("title = %s")
            movie_params.append(body.title.strip())

        if body.genres_str:
            movie_sets.append("genres_orig = %s")
            movie_params.append(body.genres_str.strip())

        if body.release_year is not None:
            movie_sets.append("release_year = %s")
            movie_params.append(body.release_year)

        if body.country is not None:
            movie_sets.append("country = %s")
            movie_params.append(body.country)

        if body.total_episodes is not None:
            movie_sets.append("total_episodes = %s")
            movie_params.append(body.total_episodes)

        if body.description is not None:
            movie_sets.append("description = %s")
            movie_params.append(body.description)

        if body.poster_url is not None:  # BUG #2 FIX: cho phép cập nhật poster_url qua PUT
            movie_sets.append("poster_url = %s")
            movie_params.append(body.poster_url)

        if movie_sets:
            movie_params.append(movie_id)
            cur.execute(
                f"UPDATE movies SET {', '.join(movie_sets)} WHERE movie_id = %s",
                movie_params,
            )

        # ── Cập nhật bảng movie_genres (chỉ khi genres_str thay đổi) ──
        if body.genres_str:
            genres_encoded = encode_genres(body.genres_str)
            genre_sets = [f"{col} = %s" for col in ALL_GENRE_COLS]
            genre_params = [genres_encoded[c] for c in ALL_GENRE_COLS] + [movie_id]
            cur.execute(
                f"UPDATE movie_genres SET {', '.join(genre_sets)} WHERE movie_id = %s",
                genre_params,
            )
            # Nếu chưa có row trong movie_genres (phim cũ trước migration), INSERT
            if cur.rowcount == 0:
                genre_cols = ", ".join(ALL_GENRE_COLS)
                genre_vals = ", ".join(["%s"] * len(ALL_GENRE_COLS))
                cur.execute(
                    f"INSERT INTO movie_genres (movie_id, {genre_cols}) VALUES (%s, {genre_vals})",
                    [movie_id] + [genres_encoded[c] for c in ALL_GENRE_COLS],
                )

        conn.commit()
        print(f"[ADMIN] Updated movie {movie_id}")
        return {"message": f"Cập nhật Movie {movie_id} thành công."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lỗi cập nhật: {e}")
    finally:
        cur.close()
        conn.close()


# ── DELETE /admin/movies/{movie_id} ───────────────────────────
@router.delete("/{movie_id}")
async def delete_movie(movie_id: int, admin: dict = Depends(require_admin)):
    """
    Xóa phim.
    - movie_genres bị xóa tự động (ON DELETE CASCADE).
    - ratings bị xóa tự động (ON DELETE CASCADE).
    - BUG FIX: Xóa file poster và video vật lý trên disk.
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Lấy thông tin file cần xóa trước khi xóa record
        cur.execute("SELECT COUNT(*) FROM ratings WHERE movie_id = %s", (movie_id,))
        ratings_count = cur.fetchone()[0]

        # Lấy poster_url và danh sách video
        cur.execute("SELECT poster_url FROM movies WHERE movie_id = %s", (movie_id,))
        movie_row = cur.fetchone()
        if not movie_row:
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")
        poster_url = movie_row[0]

        cur.execute("SELECT video_url FROM movie_videos WHERE movie_id = %s", (movie_id,))
        video_urls = [r[0] for r in cur.fetchall()]

        # Xóa record (cascade xóa movie_genres, ratings, movie_videos)
        cur.execute(
            "DELETE FROM movies WHERE movie_id = %s RETURNING movie_id, title",
            (movie_id,),
        )
        row = cur.fetchone()
        conn.commit()

        # Xóa file vật lý sau khi commit thành công
        BASE_DIR_DEL = Path(__file__).resolve().parent.parent.parent.parent
        if poster_url and poster_url.startswith('/api/uploads/'):
            poster_path = BASE_DIR_DEL / poster_url.lstrip('/api/')
            if poster_path.exists():
                try:
                    poster_path.unlink()
                except Exception:
                    pass

        for vurl in video_urls:
            if vurl and vurl.startswith('/api/uploads/'):
                vpath = BASE_DIR_DEL / vurl.lstrip('/api/')
                if vpath.exists():
                    try:
                        vpath.unlink()
                    except Exception:
                        pass

        print(f"[ADMIN] Deleted movie {movie_id} ('{row[1]}'), {ratings_count} ratings cascade-deleted.")
        return {
            "message":         f"Đã xóa phim '{row[1]}' thành công.",
            "movie_id":        row[0],
            "ratings_deleted": ratings_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lỗi xóa: {e}")
    finally:
        cur.close()
        conn.close()


# ── POST /admin/movies/{movie_id}/poster ───────────────────────
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE    = 5 * 1024 * 1024  # 5 MB

@router.post("/{movie_id}/poster")
async def upload_poster(
    movie_id: int,
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """Upload ảnh poster cho phim (JPG/PNG/WEBP, tối đa 5MB)."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Chỉ hỗ trợ: {', '.join(ALLOWED_EXT)}")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(400, "File vượt quá 5MB.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Lấy poster cũ để xóa sau khi upload thành công
        cur.execute("SELECT movie_id, poster_url FROM movies WHERE movie_id = %s", (movie_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Phim không tồn tại.")
        old_poster_url = row[1]

        filename = f"{movie_id}_{uuid.uuid4().hex}.{ext}"
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        filepath = BASE_DIR / "uploads" / "posters" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(contents)

        poster_url = f"/api/uploads/posters/{filename}"
        cur.execute("UPDATE movies SET poster_url = %s WHERE movie_id = %s", (poster_url, movie_id))
        conn.commit()

        # BUG FIX: Xóa poster cũ trên disk sau khi commit thành công
        if old_poster_url and old_poster_url.startswith('/api/uploads/posters/'):
            old_path = BASE_DIR / old_poster_url.lstrip('/api/')
            if old_path.exists():
                try:
                    old_path.unlink()
                except Exception:
                    pass

        print(f"[ADMIN] Poster uploaded for movie {movie_id}: {poster_url}")
        return {"msg": "Upload thành công", "poster_url": poster_url}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()

