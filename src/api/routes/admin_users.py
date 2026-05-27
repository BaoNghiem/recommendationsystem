"""
Admin User Management Routes: /admin/users, /admin/stats
=========================================================
- GET    /admin/stats            — System overview statistics
- GET    /admin/users/           — User list + pagination + search + filter
- GET    /admin/users/{id}       — User detail (no password_hash)
- PATCH  /admin/users/{id}/role  — Update role (user/admin)
- PATCH  /admin/users/{id}/active — Toggle is_active
- DELETE /admin/users/{id}       — Delete user (real only, ratings cascade)

Security:
  - Never SELECT or return password_hash
  - All endpoints require role = admin
"""
import time
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import require_admin

logger = logging.getLogger("movieai.admin")

router = APIRouter(prefix="/admin", tags=["Admin"])

# ── Cột an toàn (KHÔNG bao gồm password_hash) ─────────────
SAFE_COLS = "user_id, email, role, account_type, is_active, email_verified, created_at"
SAFE_COLS_LIST = [c.strip() for c in SAFE_COLS.split(",")]


def row_to_dict(row) -> dict:
    """Chuyển tuple DB → dict, serialize datetime."""
    d = dict(zip(SAFE_COLS_LIST, row))
    if d.get("created_at"):
        d["created_at"] = d["created_at"].isoformat()
    return d


# ── Pydantic schemas ───────────────────────────────────────
class RoleUpdate(BaseModel):
    role: str  # "user" | "admin"

class ActiveUpdate(BaseModel):
    is_active: bool


# ══════════════════════════════════════════════════════════════
# GET /admin/stats — System overview statistics
# ══════════════════════════════════════════════════════════════
@router.get("/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    """System-wide statistics."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM movies")
        total_movies = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ratings")
        total_ratings = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE account_type = 'real'")
        real_users = cur.fetchone()[0]

        # Phan bo rating theo sao (0.5 -> 5.0)
        cur.execute("""
            SELECT ROUND(rating * 2) / 2 AS star, COUNT(*) AS cnt
            FROM ratings
            GROUP BY star
            ORDER BY star
        """)
        dist_rows = cur.fetchall()
        rating_distribution = {str(r[0]): r[1] for r in dist_rows}

        # Top 5 phim nhieu rating nhat
        cur.execute("""
            SELECT m.title, COUNT(*) AS cnt
            FROM ratings r JOIN movies m ON r.movie_id = m.movie_id
            GROUP BY m.title ORDER BY cnt DESC LIMIT 5
        """)
        top_rated_movies = [{"title": r[0], "count": r[1]} for r in cur.fetchall()]

        return {
            "total_movies": total_movies,
            "total_ratings": total_ratings,
            "total_users": total_users,
            "real_users": real_users,
            "rating_distribution": rating_distribution,
            "top_rated_movies": top_rated_movies,
            "ts": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# GET /admin/users/ — User list + Pagination + Search + Filter
# ══════════════════════════════════════════════════════════════
@router.get("/users/")
async def list_users(
    page:         int = Query(1, ge=1),
    limit:        int = Query(20, ge=1, le=100),
    q:            str = Query("", description="Tìm theo email"),
    account_type: str = Query("", description="Filter: legacy | real | (trống = tất cả)"),
    admin: dict = Depends(require_admin),
):
    """
    Danh sách users có phân trang, tìm kiếm theo email,
    và lọc theo account_type (legacy/real).
    """
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Xây dựng WHERE động
        conditions = []
        params = []

        if q:
            conditions.append("email ILIKE %s")
            params.append(f"%{q}%")

        if account_type in ("legacy", "real"):
            conditions.append("account_type = %s")
            params.append(account_type)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Count total
        cur.execute(f"SELECT COUNT(*) FROM users {where_clause}", params)
        total = cur.fetchone()[0]

        # Fetch page
        cur.execute(
            f"""SELECT {SAFE_COLS} FROM users
                {where_clause}
                ORDER BY user_id DESC
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = cur.fetchall()
        users = [row_to_dict(r) for r in rows]

        return {
            "users":       users,
            "total":       total,
            "page":        page,
            "limit":       limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# GET /admin/users/{user_id} — Chi tiết user
# ══════════════════════════════════════════════════════════════
@router.get("/users/{user_id}")
async def get_user(user_id: int, admin: dict = Depends(require_admin)):
    """Chi tiết một user (không trả password_hash)."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            f"SELECT {SAFE_COLS} FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"User {user_id} không tồn tại.")

        user = row_to_dict(row)

        # Thêm thống kê ratings
        cur.execute("SELECT COUNT(*) FROM ratings WHERE user_id = %s", (user_id,))
        user["ratings_count"] = cur.fetchone()[0]

        return user
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# PATCH /admin/users/{user_id}/role — Cập nhật role
# ══════════════════════════════════════════════════════════════
@router.patch("/users/{user_id}/role")
async def update_role(
    user_id: int,
    body: RoleUpdate,
    admin: dict = Depends(require_admin),
):
    """Thay đổi role cho user (user / admin)."""
    if body.role not in ("user", "admin"):
        raise HTTPException(400, "Role phải là 'user' hoặc 'admin'.")

    # Không cho phép tự hạ quyền chính mình
    if admin["user_id"] == user_id and body.role != "admin":
        raise HTTPException(400, "Không thể hạ quyền chính mình.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET role = %s WHERE user_id = %s RETURNING user_id, role",
            (body.role, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"User {user_id} không tồn tại.")
        conn.commit()

        logger.info("User %d role -> %s", user_id, body.role)
        return {"user_id": row[0], "role": row[1], "message": "Role updated."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# PATCH /admin/users/{user_id}/active — Toggle is_active
# ══════════════════════════════════════════════════════════════
@router.patch("/users/{user_id}/active")
async def update_active(
    user_id: int,
    body: ActiveUpdate,
    admin: dict = Depends(require_admin),
):
    """Khóa hoặc mở khóa tài khoản user."""
    # Không cho phép khóa chính mình
    if admin["user_id"] == user_id and not body.is_active:
        raise HTTPException(400, "Không thể khóa chính mình.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET is_active = %s WHERE user_id = %s RETURNING user_id, is_active",
            (body.is_active, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"User {user_id} không tồn tại.")
        conn.commit()

        status_label = "unlocked" if body.is_active else "locked"
        logger.info("User %d -> %s", user_id, status_label)
        return {
            "user_id": row[0],
            "is_active": row[1],
            "message": f"Account #{user_id} {status_label}.",
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# DELETE /admin/users/{user_id} — Xóa user (chỉ account_type=real)
# ══════════════════════════════════════════════════════════════
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """
    Xóa user. Chỉ cho phép xóa tài khoản 'real' (người dùng mới).
    Legacy users thuộc dataset gốc, không cho xóa.
    Ratings liên quan tự động xóa theo ON DELETE CASCADE.
    """
    # Không cho phép xóa chính mình
    if admin["user_id"] == user_id:
        raise HTTPException(400, "Không thể xóa chính mình.")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Kiểm tra tồn tại + account_type
        cur.execute(
            "SELECT user_id, email, account_type FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"User {user_id} không tồn tại.")

        if row[2] != "real":
            raise HTTPException(
                400,
                f"Không thể xóa Legacy User #{user_id}. "
                "Chỉ tài khoản 'real' (đăng ký mới) mới được phép xóa.",
            )

        # Đếm ratings sẽ bị cascade-delete
        cur.execute("SELECT COUNT(*) FROM ratings WHERE user_id = %s", (user_id,))
        ratings_count = cur.fetchone()[0]

        # Xóa user (ratings cascade tự động)
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()

        logger.info("Deleted user %d, %d ratings cascade-deleted.", user_id, ratings_count)
        return {
            "message": f"Da xoa tai khoan '{row[1]}' thanh cong.",
            "user_id": user_id,
            "ratings_deleted": ratings_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()
