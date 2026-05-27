"""
Movies Routes: /movies/, /movies/{movie_id}, /movies/search, /movies/genres, /movies/by-genre
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from src.api.schemas import MovieSchema
from src.database.db_config import DatabaseConnector

router = APIRouter(prefix="/movies", tags=["Movies"])

# 18 genre columns in DB (column_name -> display label)
GENRE_MAP = {
    "action": "Action", "adventure": "Adventure", "animation": "Animation",
    "childrens": "Children's", "comedy": "Comedy", "crime": "Crime",
    "documentary": "Documentary", "drama": "Drama", "fantasy": "Fantasy",
    "film_noir": "Film-Noir", "horror": "Horror", "musical": "Musical",
    "mystery": "Mystery", "romance": "Romance", "sci_fi": "Sci-Fi",
    "thriller": "Thriller", "war": "War", "western": "Western",
}


@router.get("/", response_model=List[MovieSchema])
async def get_movies(page: int = 1, limit: int = 20):
    """Danh sach phim voi Pagination."""
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT movie_id, title, genres_orig FROM movies ORDER BY movie_id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall()
        movies = [MovieSchema(movie_id=r[0], title=r[1], genres_orig=r[2]) for r in rows]
        cur.close()
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/search")
async def search_movies(q: str = Query(..., min_length=1), limit: int = 30):
    """
    Tim kiem phim theo ten (ILIKE) — tra ve ket qua phong phu
    bao gom avg_rating va vote_count de hien thi tren SearchPage grid.
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.movie_id, m.title, m.genres_orig,
                   COALESCE(ROUND(AVG(r.rating)::numeric, 1), 0) AS avg_rating,
                   COUNT(r.rating) AS vote_count
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id
            WHERE m.title ILIKE %s
            GROUP BY m.movie_id, m.title, m.genres_orig
            ORDER BY vote_count DESC, m.title
            LIMIT %s
        """, (f"%{q}%", limit))
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "movie_id": r[0], "title": r[1], "genres_orig": r[2],
                "avg_rating": float(r[3]), "vote_count": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/search/suggest")
async def search_suggest(q: str = Query(..., min_length=1), limit: int = 6):
    """
    Goi y nhanh (autocomplete dropdown) — tra ve toi da 6 phim
    de hien thi live dropdown ngay duoi thanh search.
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT movie_id, title, genres_orig FROM movies WHERE title ILIKE %s ORDER BY title LIMIT %s",
            (f"%{q}%", limit),
        )
        rows = cur.fetchall()
        cur.close()
        return [{"movie_id": r[0], "title": r[1], "genres_orig": r[2]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/genres")
async def get_genres():
    """Tra ve danh sach 18 the loai (de Frontend render genre chips)."""
    return {
        "genres": [
            {"key": k, "label": v} for k, v in GENRE_MAP.items()
        ]
    }


@router.get("/by-genre")
async def get_movies_by_genre(
    genre: str = Query(..., description="Genre column name, e.g. 'action'"),
    limit: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    """
    Loc phim theo the loai su dung 18 cot nhi phan (0/1) trong Postgres.
    Ket qua sap xep theo so luot rating giam dan (phim pho bien truoc).
    """
    # Validate genre column name (chong SQL injection)
    if genre not in GENRE_MAP:
        raise HTTPException(400, f"Genre '{genre}' khong hop le. Chon tu: {list(GENRE_MAP.keys())}")

    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        # Count total
        cur.execute(f"SELECT COUNT(*) FROM movies WHERE {genre} = 1")
        total = cur.fetchone()[0]

        # Fetch sorted by popularity (number of ratings DESC)
        cur.execute(f"""
            SELECT m.movie_id, m.title, m.genres_orig,
                   COALESCE(rc.cnt, 0) AS rating_count
            FROM movies m
            LEFT JOIN (
                SELECT movie_id, COUNT(*) AS cnt FROM ratings GROUP BY movie_id
            ) rc ON m.movie_id = rc.movie_id
            WHERE m.{genre} = 1
            ORDER BY rating_count DESC, m.title
            LIMIT %s OFFSET %s
        """, (limit, offset))
        rows = cur.fetchall()

        movies = [
            {"movie_id": r[0], "title": r[1], "genres_orig": r[2], "rating_count": r[3]}
            for r in rows
        ]

        return {
            "genre": genre,
            "genre_label": GENRE_MAP[genre],
            "total": total,
            "page": page,
            "movies": movies,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/{movie_id}", response_model=MovieSchema)
async def get_movie_detail(movie_id: int):
    """Chi tiet mot bo phim."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT movie_id, title, genres_orig FROM movies WHERE movie_id = %s",
            (movie_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            raise HTTPException(status_code=404, detail="Movie not found")
        return MovieSchema(movie_id=row[0], title=row[1], genres_orig=row[2])
    finally:
        conn.close()

