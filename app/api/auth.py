import uuid
import re
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, TokenPair, TokenRefreshRequest
from app.models.user import User, UserGroup, UserGroupEnum, ActivationToken, PasswordResetToken, RefreshToken
from app.core.security import get_password_hash, verify_password, create_access_token
from app.tasks.email import send_activation_email, send_reset_password_email
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm, UserGroupUpdate
from app.api.deps import get_admin

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
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
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

    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
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

    db_refresh_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    )
    db.add(db_refresh_token)
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == req.refresh_token))
    db_token = result.scalars().first()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    access_token = create_access_token(data={"sub": str(db_token.user_id)})

    return {"access_token": access_token, "refresh_token": req.refresh_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(req: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email, User.is_active))
    user = result.scalars().first()

    if user:
        token_str = str(uuid.uuid4())
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()
        send_reset_password_email.delay(user.email, token_str)

    return {"message": "If email exists and is active, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(req: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    if len(req.new_password) < 8 or not re.search(r"\d", req.new_password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long and contain a number")

    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == req.token))
    db_token = result.scalars().first()

    if not db_token or db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = user_result.scalars().first()

    if user:
        user.hashed_password = get_password_hash(req.new_password)
        await db.delete(db_token)
        await db.commit()

    return {"message": "Password updated successfully"}


@router.put("/users/{user_id}/group", dependencies=[Depends(get_admin)])
async def update_user_group(user_id: int, req: UserGroupUpdate, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group_result = await db.execute(select(UserGroup).where(UserGroup.name == req.group_name))
    group = group_result.scalars().first()
    if not group:
        raise HTTPException(status_code=400, detail="Invalid group name")

    user.group_id = group.id
    await db.commit()
    return {"message": "User group updated"}
