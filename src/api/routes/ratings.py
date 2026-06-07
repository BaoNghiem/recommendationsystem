"""
Ratings Routes: /ratings/me
===========================
API cho user xem lich su danh gia cua chinh minh.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.get("/me")
async def my_ratings(
    page: int = Query(1, ge=1, description="Trang hien tai (bat dau tu 1)"),
    page_size: int = Query(200, ge=1, le=500, description="So danh gia moi trang"),
    current_user: dict = Depends(get_current_user),
):
    """
    Tra ve ratings cua user dang login co phan trang.
    - page:      trang hien tai (mac dinh 1)
    - page_size: so muc moi trang (mac dinh 200 de tuong thich nguoc)
    """
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to database.")
    cur = conn.cursor()
    try:
        # Dem tong so ratings cua user
        cur.execute("SELECT COUNT(*) FROM ratings WHERE user_id = %s", (uid,))
        total = cur.fetchone()[0]

        offset = (page - 1) * page_size
        cur.execute(
            """SELECT r.movie_id, m.title, m.genres_orig, r.rating, r.timestamp, m.poster_url
               FROM ratings r
               JOIN movies m ON r.movie_id = m.movie_id
               WHERE r.user_id = %s
               ORDER BY r.timestamp DESC
               LIMIT %s OFFSET %s""",
            (uid, page_size, offset),
        )
        rows = cur.fetchall()
        ratings = []
        for r in rows:
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
                "poster_url":  r[5],
            })
        return {
            "user_id":   uid,
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     max(1, -(-total // page_size)),  # ceiling division
            "ratings":   ratings,
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
