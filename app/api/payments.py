import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.order import Order, OrderStatusEnum
from app.models.payment import Payment, PaymentStatusEnum
from app.models.user import User
from app.api.deps import get_current_user
import os

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/create-checkout-session/{order_id}")
async def create_checkout_session(order_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    result = await db.execute(query)
    order = result.scalars().first()

    if not order or order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Invalid order or order already paid")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Order #{order.id}'},
                    'unit_amount': int(order.total_amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:8000/cancel',
            metadata={'order_id': order.id, 'user_id': current_user.id}
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
