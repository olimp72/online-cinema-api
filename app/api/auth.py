from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, TokenPair
from app.models.user import User, UserGroup, UserGroupEnum
from app.core.security import get_password_hash, verify_password, create_access_token
import uuid
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    group_result = await db.execute(select(UserGroup).where(UserGroup.name == UserGroupEnum.USER))
    group = group_result.scalars().first()

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        group_id=group.id if group else None
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenPair)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not activated")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = str(uuid.uuid4())

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
