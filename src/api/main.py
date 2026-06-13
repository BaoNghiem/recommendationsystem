"""
Movie Recommender API — Entry Point
============================================================
Responsibilities:
  1. Initialize FastAPI app
  2. Configure CORS middleware
  3. Load AI Engine (Singleton)
  4. Register all routers
  5. Health/status endpoints only

All business logic lives in src/api/routes/*.
============================================================
"""
# Force UTF-8 encoding on Windows to prevent Unicode/charmap encoding errors
# This MUST run before any import that might print Vietnamese text
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import logging
import sys
import time
from pathlib import Path

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("movieai")

# ── App ────────────────────────────────────────────────────
# 2.5 GB — phai dat truoc khi them middleware
MAX_UPLOAD_BYTES = int(2.5 * 1024 * 1024 * 1024)

app = FastAPI(
    title="Movie Recommender API",
    description="Hybrid AI Movie Recommendation System",
    version="3.0.0",
)

# CORS: Wildcard for dev — auth uses Bearer header (no cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Path setup ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db_config import DatabaseConnector
from src.api.engine_wrapper import RecommendationEngine

# ── Import all Routers ─────────────────────────────────────
from src.api.routes.auth           import router as auth_router
from src.api.routes.movies         import router as movies_router
from src.api.routes.recommendations import router as rec_router
from src.api.routes.public         import router as public_router
from src.api.routes.admin_movies   import router as admin_movies_router
from src.api.routes.admin_users    import router as admin_users_router
from src.api.routes.admin_people   import router as admin_people_router
from src.api.routes.ratings        import router as ratings_router
from src.api.routes.videos         import admin_video_router, video_router, watch_router

# Inject engine into recommendations router
from src.api.routes.recommendations import set_engine as set_rec_engine

# ── Initialize AI Engine (Singleton) ───────────────────────
engine = RecommendationEngine()
set_rec_engine(engine)

# ── Register all Routers ───────────────────────────────────
app.include_router(auth_router)           # /auth/*
app.include_router(movies_router)         # /movies/*
app.include_router(rec_router)            # /recommend/*
app.include_router(public_router)         # /trending, /popular, /rate, /user-ratings
app.include_router(admin_movies_router)   # /admin/movies/*
app.include_router(admin_users_router)    # /admin/stats, /admin/users/*
app.include_router(admin_people_router)   # /admin/directors/*, /admin/actors/*, /admin/movies/{id}/cast
app.include_router(ratings_router)        # /ratings/me
app.include_router(admin_video_router)    # /admin/movies/{id}/video
app.include_router(video_router)          # /videos/{id}/info, /videos/{id}/stream
app.include_router(watch_router)          # /watch/progress, /watch/history, /watch/continue

# ── Serve uploaded files (posters + videos) ───────────────
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
(UPLOADS_DIR / "posters").mkdir(exist_ok=True)
(UPLOADS_DIR / "videos").mkdir(exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

logger.info("=" * 60)
logger.info("  ALL ROUTERS REGISTERED:")
logger.info("     /auth/*            (Auth: login, register, verify)")
logger.info("     /movies/*          (Movies: list, search+cast, detail+cast)")
logger.info("     /recommend/*       (AI Recommendations)")
logger.info("     /trending, /popular, /rate, /user-ratings")
logger.info("     /admin/stats       (Admin: system stats)")
logger.info("     /admin/movies/*    (Admin: Movie CRUD + Cast + Video)")
logger.info("     /admin/directors/* (Admin: Director CRUD)")
logger.info("     /admin/actors/*    (Admin: Actor CRUD)")
logger.info("     /admin/users/*     (Admin: User CRUD)")
logger.info("     /ratings/*         (User ratings history)")
logger.info("     /videos/*          (Video info + streaming)")
logger.info("     /watch/*           (Watch progress + history)")
logger.info("     /api/uploads/*     (Static: posters + videos)")
logger.info("=" * 60)


# ============================================================
# HEALTH & STATUS (only endpoints in main.py)
# ============================================================

@app.get("/api/v1/health")
async def health_check():
    """Confirm Frontend-Backend connectivity."""
    db_ok = False
    try:
        conn = DatabaseConnector.get_connection()
        if conn:
            db_ok = True
            conn.close()
    except Exception:
        pass

    return {
        "status": "ok",
        "message": "Backend is running and connected",
        "database": "connected" if db_ok else "disconnected",
        "ts": time.time(),
    }


@app.get("/status")
async def get_status():
    return {"running": True, "ts": time.time()}


@app.get("/test-db")
async def test_db():
    """Check Database + AI Model status."""
    result = {"database": "Unknown", "ai_model": "Unknown"}
    conn = None
    try:
        conn = DatabaseConnector.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies")
        result["movies_in_db"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ratings")
        result["ratings_in_db"] = cur.fetchone()[0]
        cur.close()
        result["database"] = "Connected"
    except Exception as e:
        result["database"] = f"Error: {e}"
    finally:
        if conn:
            conn.close()

    try:
        pred = engine.predict_rating(1, 1)
        result["ai_model"] = f"Active (pred={pred})"
    except Exception as e:
        result["ai_model"] = f"Error: {e}"

    return result


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    # h11_max_incomplete_event_size: gioi han multipart body (2.5 GB)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        # Khong co gioi han body size o cap uvicorn — starlette tu xu ly
    )
