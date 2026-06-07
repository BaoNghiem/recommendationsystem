"""
Admin People Routes: /admin/directors, /admin/actors
======================================================
CRUD cho dao dien va dien vien + gan vao phim.

Endpoints:
  GET    /admin/directors/              — danh sach dao dien (co search + pagination)
  POST   /admin/directors/              — them moi
  PUT    /admin/directors/{id}          — sua
  DELETE /admin/directors/{id}          — xoa (cascade movie_directors)

  GET    /admin/actors/                 — danh sach dien vien
  POST   /admin/actors/                 — them moi
  PUT    /admin/actors/{id}             — sua
  DELETE /admin/actors/{id}             — xoa

  GET    /admin/movies/{id}/cast        — lay cast cua phim
  POST   /admin/movies/{id}/directors   — gan dao dien vao phim
  DELETE /admin/movies/{id}/directors/{director_id}  — go
  POST   /admin/movies/{id}/actors      — gan dien vien vao phim
  DELETE /admin/movies/{id}/actors/{actor_id}        — go
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin - People"])


# ── Pydantic schemas ────────────────────────────────────────────
class DirectorCreate(BaseModel):
    name:        str
    birth_year:  Optional[int] = None
    nationality: Optional[str] = None


class DirectorUpdate(BaseModel):
    name:        Optional[str] = None
    birth_year:  Optional[int] = None
    nationality: Optional[str] = None


class ActorCreate(BaseModel):
    name:        str
    birth_year:  Optional[int] = None
    nationality: Optional[str] = None


class ActorUpdate(BaseModel):
    name:        Optional[str] = None
    birth_year:  Optional[int] = None
    nationality: Optional[str] = None


class AssignDirector(BaseModel):
    director_id: int


class AssignActor(BaseModel):
    actor_id:       int
    character_name: Optional[str] = None
    billing_order:  Optional[int] = 99


# ── Helpers ─────────────────────────────────────────────────────
def _row_to_director(r) -> dict:
    return {"director_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3]}


def _row_to_actor(r) -> dict:
    return {"actor_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3]}


# ══════════════════════════════════════════════════════════════════
#  DIRECTORS
# ══════════════════════════════════════════════════════════════════

@router.get("/directors/")
async def list_directors(
    q:     str = Query(""),
    page:  int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin),
):
    """Danh sach dao dien co phan trang va tim kiem."""
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        if q:
            pat = f"%{q}%"
            cur.execute("SELECT COUNT(*) FROM directors WHERE name ILIKE %s", (pat,))
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT director_id, name, birth_year, nationality FROM directors "
                "WHERE name ILIKE %s ORDER BY name LIMIT %s OFFSET %s",
                (pat, limit, offset),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM directors")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT director_id, name, birth_year, nationality FROM directors "
                "ORDER BY name LIMIT %s OFFSET %s",
                (limit, offset),
            )
        rows = cur.fetchall()
        return {
            "directors":   [_row_to_director(r) for r in rows],
            "total":       total,
            "page":        page,
            "total_pages": max(1, (total + limit - 1) // limit),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.post("/directors/", status_code=201)
async def create_director(body: DirectorCreate, admin: dict = Depends(require_admin)):
    """Them dao dien moi."""
    if not body.name.strip():
        raise HTTPException(400, "Ten dao dien khong duoc de trong.")
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO directors (name, birth_year, nationality) VALUES (%s, %s, %s) "
            "RETURNING director_id",
            (body.name.strip(), body.birth_year, body.nationality),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Da them dao dien.", "director_id": new_id, "name": body.name.strip()}
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.put("/directors/{director_id}")
async def update_director(
    director_id: int,
    body: DirectorUpdate,
    admin: dict = Depends(require_admin),
):
    """Sua thong tin dao dien."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        sets, params = [], []
        if body.name is not None:
            if not body.name.strip():
                raise HTTPException(400, "Ten khong duoc de trong.")
            sets.append("name = %s"); params.append(body.name.strip())
        if body.birth_year is not None:
            sets.append("birth_year = %s"); params.append(body.birth_year)
        if body.nationality is not None:
            sets.append("nationality = %s"); params.append(body.nationality)
        if not sets:
            raise HTTPException(400, "Khong co truong nao de cap nhat.")
        params.append(director_id)
        cur.execute(
            f"UPDATE directors SET {', '.join(sets)} WHERE director_id = %s RETURNING director_id",
            params,
        )
        if not cur.fetchone():
            raise HTTPException(404, f"Director {director_id} khong ton tai.")
        conn.commit()
        return {"message": f"Da cap nhat director #{director_id}."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.delete("/directors/{director_id}")
async def delete_director(director_id: int, admin: dict = Depends(require_admin)):
    """Xoa dao dien (tu dong xoa lien ket movie_directors)."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM directors WHERE director_id = %s RETURNING name",
            (director_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"Director {director_id} khong ton tai.")
        conn.commit()
        return {"message": f"Da xoa dao dien '{row[0]}'."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════════
#  ACTORS
# ══════════════════════════════════════════════════════════════════

@router.get("/actors/")
async def list_actors(
    q:     str = Query(""),
    page:  int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin),
):
    """Danh sach dien vien co phan trang va tim kiem."""
    offset = (page - 1) * limit
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        if q:
            pat = f"%{q}%"
            cur.execute("SELECT COUNT(*) FROM actors WHERE name ILIKE %s", (pat,))
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT actor_id, name, birth_year, nationality FROM actors "
                "WHERE name ILIKE %s ORDER BY name LIMIT %s OFFSET %s",
                (pat, limit, offset),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM actors")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT actor_id, name, birth_year, nationality FROM actors "
                "ORDER BY name LIMIT %s OFFSET %s",
                (limit, offset),
            )
        rows = cur.fetchall()
        return {
            "actors":      [_row_to_actor(r) for r in rows],
            "total":       total,
            "page":        page,
            "total_pages": max(1, (total + limit - 1) // limit),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.post("/actors/", status_code=201)
async def create_actor(body: ActorCreate, admin: dict = Depends(require_admin)):
    """Them dien vien moi."""
    if not body.name.strip():
        raise HTTPException(400, "Ten dien vien khong duoc de trong.")
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO actors (name, birth_year, nationality) VALUES (%s, %s, %s) "
            "RETURNING actor_id",
            (body.name.strip(), body.birth_year, body.nationality),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"message": "Da them dien vien.", "actor_id": new_id, "name": body.name.strip()}
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.put("/actors/{actor_id}")
async def update_actor(
    actor_id: int,
    body: ActorUpdate,
    admin: dict = Depends(require_admin),
):
    """Sua thong tin dien vien."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        sets, params = [], []
        if body.name is not None:
            if not body.name.strip():
                raise HTTPException(400, "Ten khong duoc de trong.")
            sets.append("name = %s"); params.append(body.name.strip())
        if body.birth_year is not None:
            sets.append("birth_year = %s"); params.append(body.birth_year)
        if body.nationality is not None:
            sets.append("nationality = %s"); params.append(body.nationality)
        if not sets:
            raise HTTPException(400, "Khong co truong nao de cap nhat.")
        params.append(actor_id)
        cur.execute(
            f"UPDATE actors SET {', '.join(sets)} WHERE actor_id = %s RETURNING actor_id",
            params,
        )
        if not cur.fetchone():
            raise HTTPException(404, f"Actor {actor_id} khong ton tai.")
        conn.commit()
        return {"message": f"Da cap nhat actor #{actor_id}."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.delete("/actors/{actor_id}")
async def delete_actor(actor_id: int, admin: dict = Depends(require_admin)):
    """Xoa dien vien (tu dong xoa lien ket movie_actors)."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM actors WHERE actor_id = %s RETURNING name", (actor_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, f"Actor {actor_id} khong ton tai.")
        conn.commit()
        return {"message": f"Da xoa dien vien '{row[0]}'."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════════
#  MOVIE CAST MANAGEMENT  /admin/movies/{id}/cast
# ══════════════════════════════════════════════════════════════════

def _get_movie_cast(cur, movie_id: int) -> dict:
    """Helper: lay danh sach dao dien + dien vien cua phim."""
    cur.execute("""
        SELECT d.director_id, d.name, d.birth_year, d.nationality
        FROM directors d
        JOIN movie_directors md ON d.director_id = md.director_id
        WHERE md.movie_id = %s
        ORDER BY d.name
    """, (movie_id,))
    directors = [{"director_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3]}
                 for r in cur.fetchall()]

    cur.execute("""
        SELECT a.actor_id, a.name, a.birth_year, a.nationality,
               ma.character_name, ma.billing_order
        FROM actors a
        JOIN movie_actors ma ON a.actor_id = ma.actor_id
        WHERE ma.movie_id = %s
        ORDER BY ma.billing_order, a.name
    """, (movie_id,))
    actors = [{"actor_id": r[0], "name": r[1], "birth_year": r[2], "nationality": r[3],
               "character_name": r[4], "billing_order": r[5]}
              for r in cur.fetchall()]
    return {"directors": directors, "actors": actors}


@router.get("/movies/{movie_id}/cast")
async def get_movie_cast(movie_id: int, admin: dict = Depends(require_admin)):
    """Lay toan bo cast (dao dien + dien vien) cua mot phim."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Movie {movie_id} khong ton tai.")
        return _get_movie_cast(cur, movie_id)
    finally:
        cur.close(); conn.close()


@router.post("/movies/{movie_id}/directors")
async def assign_director(
    movie_id: int,
    body: AssignDirector,
    admin: dict = Depends(require_admin),
):
    """Gan dao dien vao phim (bo qua neu da ton tai)."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        # Kiem tra ton tai
        cur.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Movie {movie_id} khong ton tai.")
        cur.execute("SELECT director_id FROM directors WHERE director_id = %s", (body.director_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Director {body.director_id} khong ton tai.")

        cur.execute(
            "INSERT INTO movie_directors (movie_id, director_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (movie_id, body.director_id),
        )
        conn.commit()
        cast = _get_movie_cast(cur, movie_id)
        return {"message": "Da gan dao dien vao phim.", **cast}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.delete("/movies/{movie_id}/directors/{director_id}")
async def remove_director(
    movie_id: int,
    director_id: int,
    admin: dict = Depends(require_admin),
):
    """Go dao dien khoi phim."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM movie_directors WHERE movie_id = %s AND director_id = %s",
            (movie_id, director_id),
        )
        conn.commit()
        cast = _get_movie_cast(cur, movie_id)
        return {"message": "Da go dao dien khoi phim.", **cast}
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.post("/movies/{movie_id}/actors")
async def assign_actor(
    movie_id: int,
    body: AssignActor,
    admin: dict = Depends(require_admin),
):
    """Gan dien vien vao phim voi ten nhan vat va thu tu billing."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute("SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Movie {movie_id} khong ton tai.")
        cur.execute("SELECT actor_id FROM actors WHERE actor_id = %s", (body.actor_id,))
        if not cur.fetchone():
            raise HTTPException(404, f"Actor {body.actor_id} khong ton tai.")

        cur.execute("""
            INSERT INTO movie_actors (movie_id, actor_id, character_name, billing_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (movie_id, actor_id) DO UPDATE
                SET character_name = EXCLUDED.character_name,
                    billing_order  = EXCLUDED.billing_order
        """, (movie_id, body.actor_id, body.character_name, body.billing_order or 99))
        conn.commit()
        cast = _get_movie_cast(cur, movie_id)
        return {"message": "Da gan dien vien vao phim.", **cast}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()


@router.delete("/movies/{movie_id}/actors/{actor_id}")
async def remove_actor(
    movie_id: int,
    actor_id: int,
    admin: dict = Depends(require_admin),
):
    """Go dien vien khoi phim."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Cannot connect to Database.")
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM movie_actors WHERE movie_id = %s AND actor_id = %s",
            (movie_id, actor_id),
        )
        conn.commit()
        cast = _get_movie_cast(cur, movie_id)
        return {"message": "Da go dien vien khoi phim.", **cast}
    except Exception as e:
        conn.rollback(); raise HTTPException(500, str(e))
    finally:
        cur.close(); conn.close()
