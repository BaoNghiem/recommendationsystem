"""
Pydantic Schemas — Shared Models
=================================
MovieSchema      : thong tin phim co ban.
MovieDetailSchema: them avg_rating, vote_count, directors, actors.
DirectorSchema   : thong tin dao dien.
ActorSchema      : thong tin dien vien.
RateRequest      : dung cho POST /rate.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ── People ─────────────────────────────────────────────────────
class DirectorSchema(BaseModel):
    director_id: int
    name:        str
    birth_year:  Optional[int] = None
    nationality: Optional[str] = None

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    actor_id:       int
    name:           str
    birth_year:     Optional[int] = None
    nationality:    Optional[str] = None
    character_name: Optional[str] = None   # chi co khi lay qua movie
    billing_order:  Optional[int] = None

    class Config:
        from_attributes = True


# ── Movies ─────────────────────────────────────────────────────
class MovieSchema(BaseModel):
    """Schema thong tin phim tra ve cho Frontend (bao gom metadata moi)."""
    movie_id:        int
    title:           str
    genres_orig:     str
    release_year:    Optional[int]   = None
    country:         Optional[str]   = None
    total_episodes:  Optional[int]   = None
    description:     Optional[str]   = None
    poster_url:      Optional[str]   = None

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieSchema):
    """Schema chi tiet phim — them avg_rating, vote_count, directors, actors."""
    avg_rating: Optional[float]         = None
    vote_count: Optional[int]           = None
    directors:  List[DirectorSchema]    = []
    actors:     List[ActorSchema]       = []


# ── Rating ─────────────────────────────────────────────────────
class RateRequest(BaseModel):
    """Schema cho POST /rate endpoint."""
    user_id: int = 0  # Deprecated: se lay tu JWT, giu lai de khong break frontend
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating from 0.5 to 5.0")
