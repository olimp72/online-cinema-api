from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base

class UserGroupEnum(str, enum.Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"

class GenderEnum(str, enum.Enum):
    MAN = "MAN"
    WOMAN = "WOMAN"

class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(UserGroupEnum), unique=True, nullable=False)

    users = relationship("User", back_populates="group")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("user_groups.id"))

    group = relationship("UserGroup", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    activation_tokens = relationship("ActivationToken", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    info = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="activation_tokens")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="reset_tokens")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="refresh_tokens")
