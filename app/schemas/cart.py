from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.movie import MovieResponse

class CartItemCreate(BaseModel):
    movie_id: int

class CartItemResponse(BaseModel):
    id: int
    movie: MovieResponse
    added_at: datetime

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True
