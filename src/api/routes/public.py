"""
Public Routes: /trending, /popular, /rate, /user-ratings
=========================================================
Cac endpoint cong khai (khong can auth) phuc vu Homepage.
"""
import logging
import time
import traceback

from fastapi import APIRouter, HTTPException, Response, Depends
from src.api.schemas import RateRequest
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import get_current_user

logger = logging.getLogger("movieai.public")

router = APIRouter(tags=["Public"])


# ── GET /trending ──────────────────────────────────────────
@router.get("/trending")
async def get_trending(response: Response, limit: int = 15):
    """Phim pho bien nhat: avg rating cao + nhieu luot danh gia (> 50)."""
    response.headers["Cache-Control"] = "no-store"
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.movie_id, m.title, m.genres_orig, m.poster_url,
                   ROUND(AVG(r.rating)::numeric, 1) AS avg_rating,
                   COUNT(r.rating) AS vote_count
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id, m.title, m.genres_orig, m.poster_url
            HAVING COUNT(r.rating) > 50
            ORDER BY AVG(r.rating) DESC, COUNT(r.rating) DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "movie_id": r[0], "title": r[1], "genres_orig": r[2], "poster_url": r[3],
                "avg_rating": float(r[4]), "vote_count": r[5],
            }
            for r in rows
        ]
    finally:
        cur.close()
        conn.close()


# ── GET /latest ────────────────────────────────────────────
@router.get("/latest")
async def get_latest(response: Response, limit: int = 10):
    """10 phim moi nhat duoc them vao he thong (theo movie_id giam dan)."""
    response.headers["Cache-Control"] = "no-store"
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT movie_id, title, genres_orig, poster_url
            FROM movies
            WHERE title IS NOT NULL AND title != ''
            ORDER BY movie_id DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "movie_id": r[0], "title": r[1], "genres_orig": r[2] or "",
                "poster_url": r[3],
            }
            for r in rows
        ]
    finally:
        cur.close()
        conn.close()


# ── GET /popular ───────────────────────────────────────────
@router.get("/popular")
async def get_popular(response: Response, limit: int = 20):
    """Popularity-based Recommendations cho guest (chua dang nhap)."""
    response.headers["Cache-Control"] = "no-store"
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.movie_id, m.title, m.genres_orig,
                   ROUND(AVG(r.rating)::numeric, 1) AS avg_rating,
                   COUNT(r.rating) AS vote_count
            FROM movies m
            JOIN ratings r ON m.movie_id = r.movie_id
            GROUP BY m.movie_id, m.title, m.genres_orig
            HAVING COUNT(r.rating) > 100
            ORDER BY AVG(r.rating) DESC, COUNT(r.rating) DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        return {
            "recommendations": [
                {
                    "movie_id": r[0], "title": r[1], "genres_orig": r[2],
                    "avg_rating": float(r[3]), "vote_count": r[4],
                }
                for r in rows
            ],
            "strategy": "popularity",
            "explanation": "Phim pho bien nhat",
        }
    finally:
        conn.close()


# ── GET /user-ratings/{user_id} ────────────────────────────
@router.get("/user-ratings/{user_id}")
async def get_user_ratings(
    user_id: int,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """Tra ve tat ca rating ma User da luu trong DB (dict: movie_id -> rating)."""
    response.headers["Cache-Control"] = "no-store"
    uid = current_user["user_id"]

    # BUG #3 FIX: IDOR Protection — chi cho phep xem rating cua chinh minh
    if uid != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only view your own ratings."
        )

    conn = DatabaseConnector.get_connection()
    if not conn:
        return {}
    cur = conn.cursor()
    try:
        cur.execute("SELECT movie_id, rating FROM ratings WHERE user_id = %s", (uid,))
        rows = cur.fetchall()
        ratings_map = {r[0]: float(r[1]) for r in rows}
        logger.debug("User %d: %d rated movies", uid, len(ratings_map))
        return ratings_map
    except Exception as e:
        logger.error("User ratings error: %s", e)
        return {}
    finally:
        cur.close()
        conn.close()


# ── POST /rate ─────────────────────────────────────────────
@router.post("/rate")
async def rate_movie(data: RateRequest, current_user: dict = Depends(get_current_user)):
    """UPSERT rating. Tra ve tin hieu de Frontend biet can refresh goi y."""
    uid = current_user["user_id"]  # Lay user_id tu JWT, khong tin client
    mid = data.movie_id
    rat = data.rating
    ts = int(time.time())

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO ratings (user_id, movie_id, rating, timestamp) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (user_id, movie_id) "
            "DO UPDATE SET rating = EXCLUDED.rating, timestamp = EXCLUDED.timestamp",
            (uid, mid, rat, ts),
        )
        conn.commit()
        logger.debug("Rate OK: User %d -> Movie %d -> %.1f stars", uid, mid, rat)

        # BUG #8 FIX: Dung engine da duoc inject vao recommendations module
        # thay vi goi RecommendationEngine() constructor (Singleton nhung pattern kho hieu)
        try:
            from src.api.routes.recommendations import recommender_engine
            if recommender_engine is not None:
                recommender_engine.invalidate_fold_in_cache(uid)
        except Exception:
            pass  # Khong de loi cache anh huong den rating

        return {
            "status": "success",
            "user_id": uid,
            "movie_id": mid,
            "rating": rat,
            "recommendation_stale": True,
        }
    except Exception as e1:
        conn.rollback()
        logger.warning("UPSERT failed, trying fallback: %s", e1)

        # Fallback: DELETE then INSERT
        try:
            cur.execute("DELETE FROM ratings WHERE user_id = %s AND movie_id = %s", (uid, mid))
            cur.execute(
                "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES (%s, %s, %s, %s)",
                (uid, mid, rat, ts),
            )
            conn.commit()
            logger.debug("Rate OK via fallback: User %d -> Movie %d -> %.1f stars", uid, mid, rat)
            return {
                "status": "success",
                "user_id": uid,
                "movie_id": mid,
                "rating": rat,
                "recommendation_stale": True,
            }
        except Exception as e2:
            conn.rollback()
            logger.error("Rate fallback also failed: %s", e2)
            raise HTTPException(status_code=500, detail=str(e2))
    finally:
        cur.close()
        conn.close()
