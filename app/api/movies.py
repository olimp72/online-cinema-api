from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.db.database import get_db
from app.schemas.movie import MovieCreate, MovieResponse
from app.models.movie import Movie, Genre

router = APIRouter()


@router.get("/", response_model=List[MovieResponse])
async def get_movies(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    query = select(Movie).options(selectinload(Movie.genres)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):
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
        certification_id=movie_in.certification_id
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
        raise HTTPException(status_code=400, detail="Error creating movie. Check unique constraints or relationships.")

    return new_movie
