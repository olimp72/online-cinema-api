from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_moderator
from app.db.database import get_db
from app.models.movie import Genre, Movie
from app.models.movie_activity import Favorite, Rating
from app.models.order import OrderItem
from app.models.user import User
from app.schemas.movie import MovieCreate, MovieResponse
from sqlalchemy import or_
from typing import Optional

router = APIRouter()


# --- Pydantic Schemas ---

class RatingCreate(BaseModel):
    score: int


class CommentCreate(BaseModel):
    text: str


# --- Endpoints ---

@router.get("/", response_model=List[MovieResponse])
async def get_movies(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    year: Optional[int] = None,
    min_imdb: Optional[float] = None,
    genre_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Movie).options(selectinload(Movie.genres))

    if search:
        query = query.where(or_(Movie.name.ilike(f"%{search}%"), Movie.description.ilike(f"%{search}%")))
    if year:
        query = query.where(Movie.year == year)
    if min_imdb is not None:
        query = query.where(Movie.imdb >= min_imdb)
    if genre_id:
        query = query.where(Movie.genres.any(Genre.id == genre_id))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_in: MovieCreate,
    db: AsyncSession = Depends(get_db)
):
    new_movie = Movie(
        name=movie_in.name,
        year=movie_in.year,
        time=movie_in.time,
        imdb=movie_in.imdb,
        votes=movie_in.votes,
        meta_score=movie_in.meta_score,
        gross=movie_in.gross,
        description=movie_in.description,
        price=movie_in.price,
        certification_id=movie_in.certification_id,
    )

    if movie_in.genre_ids:
        query = select(Genre).where(Genre.id.in_(movie_in.genre_ids))
        result = await db.execute(query)
        new_movie.genres = result.scalars().all()

    db.add(new_movie)
    try:
        await db.commit()
        await db.refresh(new_movie)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating movie. Check unique constraints or relationships.",
        )

    return new_movie


@router.post("/{movie_id}/favorite", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    new_fav = Favorite(user_id=current_user.id, movie_id=movie_id)
    db.add(new_fav)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already in favorites",
        )
    return {"message": "Added to favorites"}


@router.post("/{movie_id}/rate", status_code=status.HTTP_201_CREATED)
async def rate_movie(
    movie_id: int,
    rating_in: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not (1 <= rating_in.score <= 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score must be between 1 and 10",
        )

    new_rating = Rating(
        user_id=current_user.id,
        movie_id=movie_id,
        score=rating_in.score,
    )
    db.add(new_rating)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already rated",
        )
    return {"message": "Rating added"}


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_moderator)],
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = select(OrderItem).where(OrderItem.movie_id == movie_id)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete purchased movie",
        )

    movie_query = select(Movie).where(Movie.id == movie_id)
    movie_result = await db.execute(movie_query)
    movie = movie_result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    await db.delete(movie)
    await db.commit()
