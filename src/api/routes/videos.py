"""
Video Routes — Upload, Stream & Watch History
=============================================
Admin:
  POST   /admin/movies/{id}/video               — Upload video (1 file/phim lẻ, hoặc theo tập)
  DELETE /admin/movies/{id}/video               — Xóa video phim lẻ
  DELETE /admin/movies/{id}/video/{ep}          — Xóa video tập cụ thể

Public (auth required):
  GET    /videos/{movie_id}/info                — Danh sách video/tập có sẵn
  GET    /videos/{movie_id}/stream              — Stream phim lẻ (range requests)
  GET    /videos/{movie_id}/stream/{episode_no} — Stream tập cụ thể

Watch History (auth required):
  PUT    /watch/progress                        — Lưu tiến độ xem
  GET    /watch/history                         — Lịch sử xem của user
  GET    /watch/continue                        — Danh sách phim đang xem dở
"""
import os
import uuid
import math
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter, HTTPException, Depends,
    UploadFile, File, Query, Request
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class VideoUpdateSchema(BaseModel):
    episode_no: Optional[int] = None
    episode_title: Optional[str] = None

from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import require_admin, get_current_user
from src.api.auth.utils import decode_token

# ── Routers ────────────────────────────────────────────────────
admin_video_router = APIRouter(prefix="/admin/movies", tags=["Admin - Videos"])
video_router       = APIRouter(prefix="/videos",       tags=["Videos"])
watch_router       = APIRouter(prefix="/watch",        tags=["Watch History"])

# ── Constants ──────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent.parent.parent
VIDEOS_DIR      = BASE_DIR / "uploads" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_VIDEO_EXT = {"mp4", "webm", "mkv", "avi", "mov"}
MAX_VIDEO_SIZE    = int(2.5 * 1024 * 1024 * 1024)  # 2.5 GB
CHUNK_SIZE        = 8 * 1024 * 1024                 # 8 MB — chunk streaming khi ghi file


def _get_user_from_token_param(token: str) -> dict:
    """
    Xác thực token từ query param thay vì Bearer header.
    Dùng cho /stream endpoint vì HTML5 <video> không gửi custom headers.
    """
    if not token:
        raise HTTPException(401, "Token is required.")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token invalid or expired.")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token missing user info.")
    return {"user_id": int(user_id)}


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════
def _make_video_filename(movie_id: int, season_no: int, episode_no: Optional[int], ext: str) -> str:
    if episode_no is None:
        return f"{movie_id}.{ext}"
    return f"{movie_id}_s{season_no}e{episode_no}.{ext}"


def _make_video_url(filename: str) -> str:
    return f"/api/uploads/videos/{filename}"


def _get_file_size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 2)


# ══════════════════════════════════════════════════════════════
# ADMIN — VIDEO UPLOAD / DELETE
# ══════════════════════════════════════════════════════════════

@admin_video_router.post("/{movie_id}/video", status_code=201)
async def upload_video(
    movie_id:   int,
    file:       UploadFile = File(...),
    episode_no: Optional[int] = Query(None, description="Số tập (bỏ trống nếu phim lẻ)"),
    season_no:  int           = Query(1,    description="Số mùa (mặc định 1)"),
    episode_title: Optional[str] = Query(None, description="Tên tập (tuỳ chọn)"),
    admin:      dict          = Depends(require_admin),
):
    """
    Upload video cho phim lẻ hoặc 1 tập cụ thể.
    - Phim lẻ:  episode_no để trống
    - Phim bộ:  truyền episode_no=1, episode_no=2, ...
    """
    # Validate extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(400, f"Chỉ hỗ trợ: {', '.join(ALLOWED_VIDEO_EXT)}")

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # Kiểm tra phim tồn tại
        cur.execute(
            "SELECT movie_id, title, total_episodes FROM movies WHERE movie_id = %s",
            (movie_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Phim không tồn tại.")

        total_eps = row[2]
        # Validate: phim lẻ không được upload tập
        if total_eps is None and episode_no is not None:
            raise HTTPException(400, "Phim lẻ không cần chỉ định số tập.")
        # Validate: phim bộ phải chỉ định tập
        if total_eps is not None and episode_no is None:
            raise HTTPException(400, f"Phim này có {total_eps} tập — vui lòng chỉ định episode_no.")
        
        # Validate: số tập phải lớn hơn 0
        if episode_no is not None and episode_no <= 0:
            raise HTTPException(400, "Số tập phải lớn hơn 0.")

        # Ghi file theo chunk de tranh OOM voi file lon (2.5 GB)
        filename = _make_video_filename(movie_id, season_no, episode_no, ext)
        filepath = VIDEOS_DIR / filename
        total_written = 0
        try:
            with open(filepath, "wb") as out_f:
                while True:
                    chunk = await file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    total_written += len(chunk)
                    if total_written > MAX_VIDEO_SIZE:
                        # Xoa file dang ghi do vuot qua kich thuoc cho phep
                        out_f.close()
                        filepath.unlink(missing_ok=True)
                        raise HTTPException(
                            400,
                            f"File vuot qua {MAX_VIDEO_SIZE // (1024**3)} GB."
                        )
                    out_f.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            filepath.unlink(missing_ok=True)
            raise HTTPException(500, f"Loi ghi file: {e}")

        file_size_mb = _get_file_size_mb(filepath)
        video_url    = _make_video_url(filename)

        # Upsert vào DB
        cur.execute("""
            INSERT INTO movie_videos
                (movie_id, episode_no, season_no, episode_title, video_url, file_size_mb)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (movie_id, season_no, episode_no)
            DO UPDATE SET
                video_url     = EXCLUDED.video_url,
                file_size_mb  = EXCLUDED.file_size_mb,
                episode_title = EXCLUDED.episode_title,
                uploaded_at   = NOW()
        """, (movie_id, episode_no, season_no, episode_title, video_url, file_size_mb))

        conn.commit()
        print(f"[VIDEO] Uploaded: movie={movie_id} ep={episode_no} → {filename} ({file_size_mb}MB)")
        return {
            "message":      "Upload video thành công.",
            "movie_id":     movie_id,
            "episode_no":   episode_no,
            "season_no":    season_no,
            "video_url":    video_url,
            "file_size_mb": file_size_mb,
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lỗi upload: {e}")
    finally:
        cur.close()
        conn.close()


@admin_video_router.put("/{movie_id}/video/{video_id}")
async def update_video(
    movie_id: int,
    video_id: int,
    payload: VideoUpdateSchema,
    admin: dict = Depends(require_admin),
):
    """Cập nhật thông tin tập (số tập, tiêu đề)."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("SELECT episode_no, season_no, video_url FROM movie_videos WHERE id = %s AND movie_id = %s", (video_id, movie_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy video.")
        old_ep, old_ss, old_url = row

        new_ep = payload.episode_no if payload.episode_no is not None else old_ep
        new_title = payload.episode_title

        if new_ep is not None and new_ep <= 0:
            raise HTTPException(400, "Số tập phải lớn hơn 0.")

        if new_ep != old_ep:
            cur.execute("SELECT id FROM movie_videos WHERE movie_id = %s AND season_no = %s AND episode_no = %s", (movie_id, old_ss, new_ep))
            if cur.fetchone():
                raise HTTPException(400, f"Tập số {new_ep} đã tồn tại.")

        new_url = old_url
        if new_ep != old_ep:
            ext = old_url.rsplit(".", 1)[-1]
            new_filename = _make_video_filename(movie_id, old_ss, new_ep, ext)
            new_url = _make_video_url(new_filename)

            old_filepath = VIDEOS_DIR / old_url.split("/")[-1]
            new_filepath = VIDEOS_DIR / new_filename
            
            if old_filepath.exists():
                old_filepath.replace(new_filepath)

        cur.execute("""
            UPDATE movie_videos
            SET episode_no = %s, episode_title = %s, video_url = %s
            WHERE id = %s
        """, (new_ep, new_title, new_url, video_id))

        conn.commit()
        return {"message": "Cập nhật thành công", "video_id": video_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lỗi cập nhật: {str(e)}")
    finally:
        cur.close()
        conn.close()


@admin_video_router.delete("/{movie_id}/video")
async def delete_video(
    movie_id:   int,
    episode_no: Optional[int] = Query(None),
    season_no:  int           = Query(1),
    admin:      dict          = Depends(require_admin),
):
    """Xóa video phim lẻ hoặc tập cụ thể."""
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM movie_videos
            WHERE movie_id = %s AND season_no = %s
              AND (episode_no IS NOT DISTINCT FROM %s)
            RETURNING video_url
        """, (movie_id, season_no, episode_no))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy video.")

        video_url = row[0]
        # Xóa file vật lý
        filename = video_url.split("/")[-1]
        filepath = VIDEOS_DIR / filename
        if filepath.exists():
            filepath.unlink()

        conn.commit()
        return {"message": "Đã xóa video.", "movie_id": movie_id, "episode_no": episode_no}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# PUBLIC — VIDEO INFO & STREAM
# ══════════════════════════════════════════════════════════════

@video_router.get("/{movie_id}/info")
async def get_video_info(
    movie_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Trả về danh sách video/tập có sẵn của phim.
    - Phim lẻ: list 1 phần tử với episode_no = None
    - Phim bộ: list theo thứ tự season/episode
    """
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, episode_no, season_no, episode_title,
                   video_url, duration_mins, video_quality, file_size_mb, uploaded_at
            FROM movie_videos
            WHERE movie_id = %s
            ORDER BY season_no, episode_no NULLS FIRST
        """, (movie_id,))
        rows = cur.fetchall()
        episodes = [
            {
                "id":            r[0],
                "episode_no":    r[1],
                "season_no":     r[2],
                "episode_title": r[3],
                "video_url":     r[4],
                "duration_mins": r[5],
                "video_quality": r[6],
                "file_size_mb":  r[7],
                "uploaded_at":   r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]
        return {
            "movie_id":   movie_id,
            "has_video":  len(episodes) > 0,
            "episodes":   episodes,
        }
    finally:
        cur.close()
        conn.close()


@video_router.get("/{movie_id}/stream")
async def stream_video(
    movie_id:   int,
    request:    Request,
    token:      str            = Query(..., description="JWT token (từ localStorage)"),
    episode_no: Optional[int]  = Query(None),
    season_no:  int            = Query(1),
):
    """
    Stream video với HTTP Range requests (hỗ trợ tua video).
    Token qua query param vì HTML5 <video> không thể gửi custom headers.
    - Phim lẻ:  /videos/{id}/stream?token=...
    - Tập phim: /videos/{id}/stream?token=...&episode_no=1&season_no=1
    """
    # Xác thực token từ query param
    _get_user_from_token_param(token)
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT video_url FROM movie_videos
            WHERE movie_id = %s AND season_no = %s
              AND (episode_no IS NOT DISTINCT FROM %s)
        """, (movie_id, season_no, episode_no))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Video chưa có sẵn.")

        video_url = row[0]
        filename  = video_url.split("/")[-1]
        filepath  = VIDEOS_DIR / filename

        if not filepath.exists():
            raise HTTPException(404, "File video không tồn tại trên server.")
    finally:
        cur.close()
        conn.close()

    # ── HTTP Range streaming ──────────────────────────────────
    file_size = filepath.stat().st_size
    range_header = request.headers.get("range")

    # Xác định content type
    ext = filename.rsplit(".", 1)[-1].lower()
    content_type_map = {
        "mp4":  "video/mp4",
        "webm": "video/webm",
        "mkv":  "video/x-matroska",
        "avi":  "video/x-msvideo",
        "mov":  "video/quicktime",
    }
    content_type = content_type_map.get(ext, "video/mp4")

    CHUNK_SIZE = 1024 * 1024  # 1MB per chunk

    if range_header:
        # Parse range: "bytes=start-end"
        range_str   = range_header.replace("bytes=", "")
        parts       = range_str.split("-")
        start       = int(parts[0]) if parts[0] else 0
        end         = int(parts[1]) if parts[1] else file_size - 1
        end         = min(end, file_size - 1)
        chunk_size  = end - start + 1

        def file_iterator(start, chunk_size):
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(CHUNK_SIZE, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range":  f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges":  "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type":   content_type,
        }
        return StreamingResponse(
            file_iterator(start, chunk_size),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )
    else:
        # Trả toàn bộ file
        def full_file_iterator():
            with open(filepath, "rb") as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break
                    yield data

        headers = {
            "Accept-Ranges":  "bytes",
            "Content-Length": str(file_size),
            "Content-Type":   content_type,
        }
        return StreamingResponse(
            full_file_iterator(),
            status_code=200,
            headers=headers,
            media_type=content_type,
        )


# ══════════════════════════════════════════════════════════════
# WATCH HISTORY
# ══════════════════════════════════════════════════════════════

class WatchProgressRequest(BaseModel):
    movie_id:           int
    episode_no:         Optional[int] = None
    season_no:          int           = 1
    last_position_secs: int           = 0    # giây đang dừng
    duration_secs:      int           = 1    # tổng thời lượng (để tính %)


@watch_router.put("/progress")
async def save_watch_progress(
    body:         WatchProgressRequest,
    current_user: dict = Depends(get_current_user),
):
    """Lưu tiến độ xem (gọi mỗi 10-15s từ player)."""
    uid = current_user["user_id"]
    percent = min(body.last_position_secs / max(body.duration_secs, 1), 1.0)
    is_completed = percent >= 0.85  # coi là đã xem xong khi đạt 85%

    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO watch_history
                (user_id, movie_id, episode_no, season_no,
                 last_position_secs, watch_percent, is_completed, watched_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, movie_id, season_no, COALESCE(episode_no, 0))
            DO UPDATE SET
                last_position_secs  = EXCLUDED.last_position_secs,
                watch_percent       = EXCLUDED.watch_percent,
                is_completed        = EXCLUDED.is_completed,
                watched_at          = NOW()
        """, (uid, body.movie_id, body.episode_no, body.season_no,
              body.last_position_secs, round(percent, 4), is_completed))
        conn.commit()
        return {
            "saved":        True,
            "watch_percent": round(percent * 100, 1),
            "is_completed": is_completed,
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()


@watch_router.get("/history")
async def get_watch_history(
    page:         int  = Query(1, ge=1),
    page_size:    int  = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Lịch sử xem đầy đủ của user (có phân trang)."""
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        # BUG FIX: Dem so PHIM rieng biet (distinct movie_id), khong phai tong so entries
        # Vi mot phim bo co nhieu tap se tao nhieu entries trong watch_history
        cur.execute("SELECT COUNT(DISTINCT movie_id) FROM watch_history WHERE user_id = %s", (uid,))
        total = cur.fetchone()[0]

        offset = (page - 1) * page_size
        cur.execute("""
            WITH recent AS (
                SELECT DISTINCT ON (movie_id) *
                FROM watch_history
                WHERE user_id = %s
                ORDER BY movie_id, watched_at DESC
            )
            SELECT r.movie_id, m.title, m.genres_orig, m.poster_url,
                   r.episode_no, r.season_no,
                   r.last_position_secs, r.watch_percent, r.is_completed,
                   r.watched_at
            FROM recent r
            JOIN movies m ON r.movie_id = m.movie_id
            ORDER BY r.watched_at DESC
            LIMIT %s OFFSET %s
        """, (uid, page_size, offset))
        rows = cur.fetchall()
        history = [
            {
                "movie_id":           r[0],
                "title":              r[1],
                "genres_orig":        r[2],
                "poster_url":         r[3],
                "episode_no":         r[4],
                "season_no":          r[5],
                "last_position_secs": r[6],
                "watch_percent":      round(float(r[7]) * 100, 1),
                "is_completed":       r[8],
                "watched_at":         r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ]
        return {
            "user_id":   uid,
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "pages":     math.ceil(total / page_size) if total else 1,
            "history":   history,
        }
    finally:
        cur.close()
        conn.close()

@watch_router.get("/history/{movie_id}")
async def get_watch_history_for_movie(
    movie_id:     int,
    current_user: dict = Depends(get_current_user),
):
    """Lấy danh sách các tập đã xem của 1 bộ phim."""
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "DB ERROR")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT episode_no, season_no, last_position_secs, watch_percent, is_completed
            FROM watch_history
            WHERE user_id = %s AND movie_id = %s
            ORDER BY watched_at DESC
        """, (uid, movie_id))
        rows = cur.fetchall()
        return {
            "movie_id": movie_id,
            "history": [
                {
                    "episode_no": r[0],
                    "season_no": r[1],
                    "last_position_secs": r[2],
                    "watch_percent": round(float(r[3]) * 100, 1),
                    "is_completed": r[4]
                }
                for r in rows
            ]
        }
    finally:
        cur.close()
        conn.close()


@watch_router.get("/continue")
async def get_continue_watching(
    limit:        int  = Query(10, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):
    """
    Danh sách phim đang xem dở (chưa hoàn thành) — dùng cho row 'Xem tiếp' ở Home.
    Sắp xếp theo watched_at DESC (xem gần nhất lên đầu).
    """
    uid = current_user["user_id"]
    conn = DatabaseConnector.get_connection()
    if not conn:
        raise HTTPException(503, "Không thể kết nối Database.")
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT wh.movie_id, m.title, m.genres_orig, m.poster_url,
                   m.total_episodes,
                   wh.episode_no, wh.season_no,
                   wh.last_position_secs, wh.watch_percent,
                   wh.watched_at
            FROM watch_history wh
            JOIN movies m ON wh.movie_id = m.movie_id
            WHERE wh.user_id = %s AND wh.is_completed = FALSE
            ORDER BY wh.watched_at DESC
            LIMIT %s
        """, (uid, limit))
        rows = cur.fetchall()
        return {
            "user_id": uid,
            "items": [
                {
                    "movie_id":           r[0],
                    "title":              r[1],
                    "genres_orig":        r[2],
                    "poster_url":         r[3],
                    "total_episodes":     r[4],
                    "episode_no":         r[5],
                    "season_no":          r[6],
                    "last_position_secs": r[7],
                    "watch_percent":      round(float(r[8]) * 100, 1),
                    "watched_at":         r[9].isoformat() if r[9] else None,
                }
                for r in rows
            ],
        }
    finally:
        cur.close()
        conn.close()
