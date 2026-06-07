"""
Movies Routes: /movies/, /movies/{movie_id}, /movies/search, /movies/genres, /movies/by-genre
Nang cap Phase 3:
  - GET /movies/{id} tra ve directors + actors.
  - GET /movies/search tim kiem theo ca ten phim, dao dien, dien vien.
  - GET /movies/by-genre van giu nguyen.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from src.api.schemas import MovieSchema, MovieDetailSchema
from src.database.db_config import DatabaseConnector

router = APIRouter(prefix="/movies", tags=["Movies"])

# 18 genre columns
GENRE_MAP = {
    "action": "Action", "adventure": "Adventure", "animation": "Animation",
    "childrens": "Children's", "comedy": "Comedy", "crime": "Crime",
    "documentary": "Documentary", "drama": "Drama", "fantasy": "Fantasy",
    "film_noir": "Film-Noir", "horror": "Horror", "musical": "Musical",
    "mystery": "Mystery", "romance": "Romance", "sci_fi": "Sci-Fi",
    "thriller": "Thriller", "war": "War", "western": "Western",
}


def _row_to_movie(r) -> dict:
    return {
        "movie_id":       r[0],
        "title":          r[1],
        "genres_orig":    r[2],
        "release_year":   r[3],
        "country":        r[4],
        "total_episodes": r[5],
        "description":    r[6],
        "poster_url":     r[7] if len(r) > 7 else None,
    }


def _fetch_cast(cur, movie_id: int) -> dict:
    """Lay directors + actors cua 1 phim."""
    cur.execute("""
        SELECT d.director_id, d.name, d.birth_year, d.nationality
        FROM directors d
        JOIN movie_directors md ON d.director_id = md.director_id
        WHERE md.movie_id = %s
        ORDER BY d.name
    """, (movie_id,))
    directors = [
        {"director_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3]}
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT a.actor_id, a.name, a.birth_year, a.nationality,
               ma.character_name, ma.billing_order
        FROM actors a
        JOIN movie_actors ma ON a.actor_id = ma.actor_id
        WHERE ma.movie_id = %s
        ORDER BY ma.billing_order, a.name
    """, (movie_id,))
    actors = [
        {"actor_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3],
         "character_name": r[4], "billing_order": r[5]}
        for r in cur.fetchall()
    ]
    return {"directors": directors, "actors": actors}


# ── GET /movies/ ───────────────────────────────────────────────
@router.get("/", response_model=List[MovieSchema])
async def get_movies(page: int = 1, limit: int = 20):
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT movie_id, title, genres_orig,
                      release_year, country, total_episodes, description, poster_url
               FROM movies ORDER BY movie_id LIMIT %s OFFSET %s""",
            (limit, offset),
        )
        rows = cur.fetchall()
        cur.close()
        return [_row_to_movie(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ── GET /movies/search ─────────────────────────────────────────
@router.get("/search")
async def search_movies(
    q:     str = Query(..., min_length=1),
    limit: int = 30,
):
    """
    Tim kiem phim theo ten, dao dien, hoac dien vien.
    Ket qua gop chung va sap xep theo luot rating giam dan.
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        pattern = f"%{q}%"
        cur.execute("""
            SELECT DISTINCT m.movie_id, m.title, m.genres_orig,
                   m.release_year, m.country, m.total_episodes, m.description, m.poster_url,
                   COALESCE(ROUND(AVG(r.rating)::numeric, 1), 0) AS avg_rating,
                   COUNT(r.rating) AS vote_count
            FROM movies m
            LEFT JOIN ratings r      ON m.movie_id  = r.movie_id
            LEFT JOIN movie_directors md ON m.movie_id = md.movie_id
            LEFT JOIN directors d    ON md.director_id = d.director_id
            LEFT JOIN movie_actors ma ON m.movie_id   = ma.movie_id
            LEFT JOIN actors a       ON ma.actor_id    = a.actor_id
            WHERE m.title  ILIKE %s
               OR d.name   ILIKE %s
               OR a.name   ILIKE %s
            GROUP BY m.movie_id, m.title, m.genres_orig,
                     m.release_year, m.country, m.total_episodes, m.description, m.poster_url
            ORDER BY vote_count DESC, m.title
            LIMIT %s
        """, (pattern, pattern, pattern, limit))
        rows = cur.fetchall()
        cur.close()
        # Them cast (directors) vao ket qua tim kiem
        results = []
        for r in rows:
            item = {
                **_row_to_movie(r[:8]),
                "avg_rating": float(r[8]),
                "vote_count":  r[9],
            }
            results.append(item)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ── GET /movies/search/suggest ────────────────────────────────
@router.get("/search/suggest")
async def search_suggest(q: str = Query(..., min_length=1), limit: int = 6):
    """Goi y nhanh (autocomplete) — tim theo ten phim, dao dien, dien vien."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
        pattern = f"%{q}%"
        cur.execute("""
            SELECT DISTINCT m.movie_id, m.title, m.genres_orig,
                   m.release_year, m.country, m.total_episodes, m.description, m.poster_url
            FROM movies m
            LEFT JOIN movie_directors md ON m.movie_id  = md.movie_id
            LEFT JOIN directors d        ON md.director_id = d.director_id
            LEFT JOIN movie_actors ma    ON m.movie_id  = ma.movie_id
            LEFT JOIN actors a           ON ma.actor_id  = a.actor_id
            WHERE m.title ILIKE %s OR d.name ILIKE %s OR a.name ILIKE %s
            ORDER BY m.title
            LIMIT %s
        """, (pattern, pattern, pattern, limit))
        rows = cur.fetchall()
        cur.close()
        return [_row_to_movie(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ── GET /movies/genres ─────────────────────────────────────────
@router.get("/genres")
async def get_genres():
    return {"genres": [{"key": k, "label": v} for k, v in GENRE_MAP.items()]}


# ── GET /movies/by-genre ──────────────────────────────────────
@router.get("/by-genre")
async def get_movies_by_genre(
    genre: str = Query(...),
    limit: int = Query(30, ge=1, le=100),
    page:  int = Query(1, ge=1),
):
    if genre not in GENRE_MAP:
        raise HTTPException(400, f"Genre '{genre}' khong hop le.")
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(f"""
            SELECT COUNT(*)
            FROM movies m
            JOIN movie_genres mg ON m.movie_id = mg.movie_id
            WHERE mg.{genre} = 1
        """)
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT m.movie_id, m.title, m.genres_orig,
                   m.release_year, m.country, m.total_episodes, m.description, m.poster_url,
                   COALESCE(rc.cnt, 0) AS rating_count
            FROM movies m
            JOIN movie_genres mg ON m.movie_id = mg.movie_id
            LEFT JOIN (
                SELECT movie_id, COUNT(*) AS cnt FROM ratings GROUP BY movie_id
            ) rc ON m.movie_id = rc.movie_id
            WHERE mg.{genre} = 1
            ORDER BY rating_count DESC, m.title
            LIMIT %s OFFSET %s
        """, (limit, offset))
        rows = cur.fetchall()
        return {
            "genre":       genre,
            "genre_label": GENRE_MAP[genre],
            "total":       total,
            "page":        page,
            "movies": [{**_row_to_movie(r[:8]), "rating_count": r[8]} for r in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close(); conn.close()


# ── GET /movies/{movie_id} ─────────────────────────────────────
@router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int):
    """
    Chi tiet phim bao gom:
    - Metadata: release_year, country, total_episodes, description
    - Community stats: avg_rating, vote_count
    - Cast: directors, actors
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    try:
        cur = conn.cursor()
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
            raise HTTPException(status_code=404, detail="Movie not found")

        cast = _fetch_cast(cur, movie_id)
        cur.close()

        return {
            **_row_to_movie(row[:8]),
            "avg_rating": float(row[8]) if row[8] is not None else None,
            "vote_count":  row[9],
            **cast,
        }
    finally:
        conn.close()
