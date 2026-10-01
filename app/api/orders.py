from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import List
from app.db.database import get_db
from app.models.order import Order, OrderItem, OrderStatusEnum
from app.models.cart import Cart
from app.models.movie import Movie
from app.models.user import User
from app.schemas.order import OrderResponse
from app.api.deps import get_current_user
from app.api.deps import get_moderator

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart_query = (
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == current_user.id)
        .with_for_update()
    )
    cart_result = await db.execute(cart_query)
    cart = cart_result.scalars().first()

    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    movie_ids = [item.movie_id for item in cart.items]
    movies_query = select(Movie).where(Movie.id.in_(movie_ids)).with_for_update()
    movies_result = await db.execute(movies_query)
    movies_map = {movie.id: movie for movie in movies_result.scalars().all()}

    total_amount = Decimal("0.00")
    order = Order(user_id=current_user.id, status=OrderStatusEnum.PENDING)
    db.add(order)
    await db.flush()

    for item in cart.items:
        movie = movies_map.get(item.movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail=f"Movie with id {item.movie_id} not found")

        order_item = OrderItem(
            order_id=order.id,
            movie_id=movie.id,
            price_at_order=movie.price
        )
        total_amount += movie.price
        db.add(order_item)
        await db.delete(item)

    order.total_amount = total_amount
    await db.commit()
    await db.refresh(order)

    return order


@router.get("/", response_model=List[OrderResponse])
async def get_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Order).options(selectinload(Order.items).selectinload(OrderItem.movie)).where(
        Order.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/all", response_model=List[OrderResponse], dependencies=[Depends(get_moderator)])
async def get_all_orders(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(Order).options(selectinload(Order.items).selectinload(OrderItem.movie)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
