from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import List
from app.db.database import get_db
from app.models.order import Order, OrderItem, OrderStatusEnum
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.schemas.order import OrderResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart_query = select(Cart).options(selectinload(Cart.items).selectinload(CartItem.movie)).where(
        Cart.user_id == current_user.id)
    cart_result = await db.execute(cart_query)
    cart = cart_result.scalars().first()

    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = Decimal("0.00")
    order = Order(user_id=current_user.id, status=OrderStatusEnum.PENDING)
    db.add(order)
    await db.flush()

    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            movie_id=item.movie.id,
            price_at_order=item.movie.price
        )
        total_amount += item.movie.price
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
