from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint, CheckConstraint
from datetime import datetime
from app.db.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_user_favorite_movie"),)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    score = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_rating_movie"),
        CheckConstraint("score >= 1 AND score <= 10", name="chk_rating_score")
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
