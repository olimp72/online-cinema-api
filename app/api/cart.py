from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.db.database import get_db
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.schemas.cart import CartResponse, CartItemCreate
from app.api.deps import get_current_user
from app.models.order import Order, OrderItem, OrderStatusEnum
from app.models.movie import Movie

router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Cart).options(
        selectinload(Cart.items).selectinload(CartItem.movie)
    ).where(Cart.user_id == current_user.id)

    result = await db.execute(query)
    cart = result.scalars().first()

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()

        result = await db.execute(query)
        cart = result.scalars().first()

    return cart


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(item_in: CartItemCreate, current_user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    movie_query = select(Movie).where(Movie.id == item_in.movie_id)
    movie_result = await db.execute(movie_query)
    if not movie_result.scalars().first():
        raise HTTPException(status_code=404, detail="Movie not found")

    purchased_query = select(OrderItem).join(Order).where(
        Order.user_id == current_user.id,
        Order.status == OrderStatusEnum.PAID,
        OrderItem.movie_id == item_in.movie_id
    )
    purchased_result = await db.execute(purchased_query)
    if purchased_result.scalars().first():
        raise HTTPException(status_code=400, detail="Movie already purchased")

    query = select(Cart).where(Cart.user_id == current_user.id)
    result = await db.execute(query)
    cart = result.scalars().first()

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(query)
            cart = result.scalars().first()

    new_item = CartItem(cart_id=cart.id, movie_id=item_in.movie_id)
    db.add(new_item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Movie already in cart")
    return {"message": "Item added to cart"}


@router.delete("/items/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(movie_id: int, current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    query = select(Cart).where(Cart.user_id == current_user.id)
    result = await db.execute(query)
    cart = result.scalars().first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item_query = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.movie_id == movie_id)
    item_result = await db.execute(item_query)
    item = item_result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    await db.delete(item)
    await db.commit()
