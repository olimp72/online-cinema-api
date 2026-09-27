from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieCreate(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal
    certification_id: int
    genre_ids: List[int] = []


class MovieResponse(BaseModel):
    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    price: Decimal
    genres: List[GenreResponse] = []

    class Config:
        from_attributes = True
