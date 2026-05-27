"""
Pydantic Schemas — Shared Models
=================================
MovieSchema: dung chung cho cac route tra ve thong tin phim.
RateRequest: dung cho POST /rate.
"""
from pydantic import BaseModel, Field
from typing import Optional


class MovieSchema(BaseModel):
    """Schema thong tin phim tra ve cho Frontend."""
    movie_id: int
    title: str
    genres_orig: str

    class Config:
        from_attributes = True


class RateRequest(BaseModel):
    """Schema cho POST /rate endpoint."""
    user_id: int = 0  # Deprecated: se lay tu JWT, giu lai de khong break frontend
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating from 0.5 to 5.0")

