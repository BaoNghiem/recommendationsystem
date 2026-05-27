"""
Admin Movie CRUD Routes: /admin/movies
- GET    /admin/movies          — Danh sách phim + pagination + search
- GET    /admin/movies/{id}     — Chi tiết 1 phim
- POST   /admin/movies          — Thêm phim mới (tự encode genres)
- PUT    /admin/movies/{id}     — Sửa phim (tự encode genres)
- DELETE /admin/movies/{id}     — Xóa phim (cascade ratings)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import require_admin

router = APIRouter(prefix="/admin/movies", tags=["Admin - Movies"])

# ── Genre mapping: tên hiển thị → tên cột DB ──────────────
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


# ── Pydantic schemas ───────────────────────────────────────
class MovieCreate(BaseModel):
    title:      str
    genres_str: str   # Ví dụ: "Action|Comedy"

class MovieUpdate(BaseModel):
    title:      Optional[str] = None
    genres_str: Optional[str] = None


# ── GET /admin/movies ──────────────────────────────────────
@router.get("/")
async def list_movies(
    page:  int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q:     str = Query("", description="Tìm theo tên phim"),
    admin: dict = Depends(require_admin),
):
    """Danh sách phim có phân trang và tìm kiếm."""
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        if q:
            pattern = f"%{q}%"
            cur.execute(
                "SELECT COUNT(*) FROM movies WHERE title ILIKE %s", (pattern,)
            )
            total = cur.fetchone()[0]
            cur.execute(
                """SELECT movie_id, title, genres_orig FROM movies
                   WHERE title ILIKE %s
                   ORDER BY movie_id DESC LIMIT %s OFFSET %s""",
                (pattern, limit, offset),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM movies")
            total = cur.fetchone()[0]
            cur.execute(
                """SELECT movie_id, title, genres_orig FROM movies
                   ORDER BY movie_id DESC LIMIT %s OFFSET %s""",
                (limit, offset),
            )

        rows = cur.fetchall()
        movies = [{"movie_id": r[0], "title": r[1], "genres_orig": r[2]} for r in rows]
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


# ── GET /admin/movies/{movie_id} ───────────────────────────
@router.get("/{movie_id}")
async def get_movie(movie_id: int, admin: dict = Depends(require_admin)):
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT movie_id, title, genres_orig FROM movies WHERE movie_id = %s",
            (movie_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")
        return {"movie_id": row[0], "title": row[1], "genres_orig": row[2]}
    finally:
        cur.close()
        conn.close()


# ── POST /admin/movies ─────────────────────────────────────
@router.post("/", status_code=201)
async def create_movie(body: MovieCreate, admin: dict = Depends(require_admin)):
    """
    Thêm phim mới. Backend tự động:
    - Gán movie_id tiếp theo (MAX + 1)
    - Encode genres_str thành các cột 0/1
    """
    # Validate dữ liệu đầu vào
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

        # Xây dựng câu INSERT động
        genre_cols   = ", ".join(ALL_GENRE_COLS)
        genre_vals   = ", ".join(["%s"] * len(ALL_GENRE_COLS))
        genre_values = [genres_encoded[c] for c in ALL_GENRE_COLS]

        cur.execute(
            f"""INSERT INTO movies (movie_id, title, genres_orig, {genre_cols})
                VALUES (%s, %s, %s, {genre_vals})
                RETURNING movie_id""",
            [new_id, body.title.strip(), body.genres_str.strip()] + genre_values,
        )
        inserted_id = cur.fetchone()[0]
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


# ── PUT /admin/movies/{movie_id} ───────────────────────────
@router.put("/{movie_id}")
async def update_movie(
    movie_id: int,
    body: MovieUpdate,
    admin: dict = Depends(require_admin),
):
    """
    Sửa tiêu đề và/hoặc thể loại. Khi sửa genres, tự động
    cập nhật lại tất cả cột 0/1 để AI gợi ý đúng.
    """
    if not body.title and not body.genres_str:
        raise HTTPException(400, "Cần ít nhất title hoặc genres_str để cập nhật.")

    # Validate dữ liệu đầu vào (không cho phép chuỗi toàn khoảng trắng)
    if body.title is not None and not body.title.strip():
        raise HTTPException(400, "Tiêu đề phim không được để trống.")
    if body.genres_str is not None and not body.genres_str.strip():
        raise HTTPException(400, "Thể loại phim không được để trống.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Kiểm tra tồn tại
        cur.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")

        set_clauses = []
        params      = []

        if body.title:
            set_clauses.append("title = %s")
            params.append(body.title.strip())

        if body.genres_str:
            set_clauses.append("genres_orig = %s")
            params.append(body.genres_str.strip())
            # Cập nhật tất cả cột genre vector
            genres_encoded = encode_genres(body.genres_str)
            for col in ALL_GENRE_COLS:
                set_clauses.append(f"{col} = %s")
                params.append(genres_encoded[col])

        params.append(movie_id)
        cur.execute(
            f"UPDATE movies SET {', '.join(set_clauses)} WHERE movie_id = %s",
            params,
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


# ── DELETE /admin/movies/{movie_id} ───────────────────────
@router.delete("/{movie_id}")
async def delete_movie(movie_id: int, admin: dict = Depends(require_admin)):
    """
    Xóa phim. Ratings liên quan bị xóa tự động (ON DELETE CASCADE).
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Đếm ratings sẽ bị xóa (để log)
        cur.execute("SELECT COUNT(*) FROM ratings WHERE movie_id = %s", (movie_id,))
        ratings_count = cur.fetchone()[0]

        cur.execute(
            "DELETE FROM movies WHERE movie_id = %s RETURNING movie_id, title",
            (movie_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"Movie {movie_id} không tồn tại.")

        conn.commit()
        print(f"[ADMIN] Deleted movie {movie_id} ('{row[1]}'), {ratings_count} ratings cascade-deleted.")
        return {
            "message":        f"Đã xóa phim '{row[1]}' thành công.",
            "movie_id":       row[0],
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
