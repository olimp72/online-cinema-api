import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.order import Order, OrderStatusEnum
from app.models.payment import Payment, PaymentStatusEnum
from app.models.user import User
from app.api.deps import get_current_user
import os
from fastapi import Request
from app.api.deps import get_moderator

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/create-checkout-session/{order_id}")
async def create_checkout_session(
        order_id: int, current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
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


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = int(session['metadata']['order_id'])

        query = select(Order).where(Order.id == order_id)
        result = await db.execute(query)
        order = result.scalars().first()

        if order:
            order.status = OrderStatusEnum.PAID

            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                amount=order.total_amount,
                status=PaymentStatusEnum.SUCCESSFUL,
                external_payment_id=session['id']
            )
            db.add(payment)
            await db.commit()

    return {"status": "success"}


@router.get("/all", dependencies=[Depends(get_moderator)])
async def get_all_payments(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(Payment).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
