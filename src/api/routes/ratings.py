"""
Ratings Routes: /ratings/me
===========================
API cho user xem lich su danh gia cua chinh minh.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.get("/me")
async def my_ratings(current_user: dict = Depends(get_current_user)):
    """
    Tra ve tat ca ratings cua user dang login,
    kem thong tin phim (title, genres) de hien thi tren Profile.
    """
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to database.")
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT r.movie_id, m.title, m.genres_orig, r.rating, r.timestamp
               FROM ratings r
               JOIN movies m ON r.movie_id = m.movie_id
               WHERE r.user_id = %s
               ORDER BY r.timestamp DESC
               LIMIT 200""",
            (uid,),
        )
        rows = cur.fetchall()
        ratings = []
        for r in rows:
            # timestamp is bigint (Unix epoch seconds), convert to ISO string
            ts = r[4]
            ts_str = None
            if ts:
                try:
                    ts_str = datetime.fromtimestamp(int(ts)).isoformat()
                except (ValueError, OSError, OverflowError):
                    ts_str = None
            ratings.append({
                "movie_id":    r[0],
                "title":       r[1],
                "genres_orig": r[2],
                "rating":      float(r[3]),
                "timestamp":   ts_str,
            })
        return {
            "user_id": uid,
            "total":   len(ratings),
            "ratings": ratings,
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
    finally:
        cur.close()
        conn.close()


@router.delete("/me/{movie_id}")
async def delete_my_rating(
    movie_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Xoa mot rating cua user dang login cho movie_id cu the.
    """
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to database.")
    cur = conn.cursor()
    try:
        # Kiem tra rating co ton tai khong
        cur.execute(
            "SELECT 1 FROM ratings WHERE user_id = %s AND movie_id = %s",
            (uid, movie_id),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Rating not found.")

        cur.execute(
            "DELETE FROM ratings WHERE user_id = %s AND movie_id = %s",
            (uid, movie_id),
        )
        conn.commit()
        print(f"[RATINGS] User {uid} deleted rating for movie {movie_id}")
        return {"message": "Rating deleted successfully.", "movie_id": movie_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Error deleting rating: {e}")
    finally:
        cur.close()
        conn.close()
