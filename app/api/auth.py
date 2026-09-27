import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, TokenPair
from app.models.user import User, UserGroup, UserGroupEnum, ActivationToken
from app.core.security import get_password_hash, verify_password, create_access_token
from app.tasks.email import send_activation_email

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
        group_id=group.id if group else None,
        is_active=False
    )
    db.add(new_user)
    await db.flush()

    token_str = str(uuid.uuid4())
    activation_token = ActivationToken(
        user_id=new_user.id,
        token=token_str,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(activation_token)
    await db.commit()
    await db.refresh(new_user)

    send_activation_email.delay(new_user.email, token_str)

    return new_user


@router.get("/activate/{token}")
async def activate_account(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ActivationToken).where(ActivationToken.token == token))
    db_token = result.scalars().first()

    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid token")

    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user_result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = user_result.scalars().first()

    if user:
        user.is_active = True
        await db.delete(db_token)
        await db.commit()

    return {"message": "Account successfully activated"}


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
