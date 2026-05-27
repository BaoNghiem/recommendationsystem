"""
Recommendations Routes: /recommend/{user_id}
=============================================
Calls RecommendationEngine (Hybrid AI) to generate personalized suggestions.
Engine is injected from main.py at startup via set_engine().

Security: JWT Guard bao ve — chi cho phep user xem goi y cua chinh minh (IDOR Protection).
"""
import logging
import time

from fastapi import APIRouter, HTTPException, Response, Depends
from src.database.db_config import DatabaseConnector
from src.api.auth.dependencies import get_current_user

logger = logging.getLogger("movieai.recommend")

router = APIRouter(prefix="/recommend", tags=["Recommendations"])

# Engine will be injected from main.py at startup
recommender_engine = None


def set_engine(engine):
    """Called from main.py to inject the loaded engine."""
    global recommender_engine
    recommender_engine = engine


# Strategy display labels for Frontend
STRATEGY_LABELS = {
    "hybrid":        "AI Hybrid (FunkSVD + Content-Based)",
    "hybrid_foldin": "AI Hybrid Fold-in (SVD Online Learning)",
    "content_based": "Content-Based (phim tuong tu ban da thich)",
    "popularity":    "Phim pho bien nhat",
}


@router.get("/{user_id}")
async def get_recommendations(
    user_id: int,
    response: Response,
    top_n: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """
    AI-powered movie recommendations.
    Routes through Hybrid Engine: FunkSVD -> Content-Based -> Popularity fallback.
    Security: Yeu cau JWT token, chi cho phep xem goi y cua chinh minh.
    """
    response.headers["Cache-Control"] = "no-store"

    if recommender_engine is None:
        raise HTTPException(status_code=503, detail="AI Model not ready.")

    # IDOR Protection: chi cho phep user xem goi y cua chinh minh
    uid = current_user["user_id"]
    if uid != int(user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only view your own recommendations."
        )

    try:
        is_known = uid in recommender_engine.user2idx
        logger.debug("User %d | Known in model: %s", uid, is_known)

        # Get already-rated movies to exclude
        rated_ids = set(recommender_engine.get_rated_movies(uid))

        # Call AI Engine — returns (movie_ids, strategy) or just list
        result = recommender_engine.get_recommendations(uid, top_n=top_n + len(rated_ids) + 10)

        if isinstance(result, tuple):
            raw_ids, strategy = result
        else:
            raw_ids, strategy = result, "unknown"

        # Filter out already-watched movies
        filtered_ids = []
        for mid in raw_ids:
            m = int(mid)
            if m not in rated_ids:
                filtered_ids.append(m)
            if len(filtered_ids) >= top_n:
                break

        if not filtered_ids:
            return {
                "user_id": uid,
                "recommendations": [],
                "strategy": strategy,
                "ts": time.time(),
            }

        # Query DB for movie details
        conn = DatabaseConnector.get_connection()
        if not conn:
            raise HTTPException(status_code=503, detail="Cannot connect to Database.")
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT movie_id, title, genres_orig FROM movies WHERE movie_id = ANY(%s)",
                (filtered_ids,),
            )
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        lookup = {r[0]: {"movie_id": r[0], "title": r[1], "genres_orig": r[2]} for r in rows}

        recs = []
        for mid in filtered_ids:
            if mid in lookup:
                item = dict(lookup[mid])
                item["predicted_rating"] = recommender_engine.predict_rating(uid, mid)
                recs.append(item)

        explanation = STRATEGY_LABELS.get(strategy, strategy)

        logger.debug("User %d: %d movies via [%s]", uid, len(recs), strategy)
        return {
            "user_id": uid,
            "recommendations": recs,
            "strategy": strategy,
            "explanation": explanation,
            "ts": time.time(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Recommendation error for user %d: %s", uid, e)
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {e}")
