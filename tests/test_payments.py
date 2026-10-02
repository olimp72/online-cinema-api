import pytest
import stripe
from unittest.mock import patch
from sqlalchemy.future import select
from app.main import app
from app.models.order import Order, OrderStatusEnum
from app.models.payment import Payment
from app.models.user import User
from app.api.deps import get_current_user
from tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def override_auth_dependencies():
    """Bypass auth system for payment tests and inject a mock current_user."""
    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="mock_user@example.com")
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def test_order():
    """Creates a standard pending order for the mock user."""
    async with TestingSessionLocal() as session:
        order = Order(user_id=1, status=OrderStatusEnum.PENDING, total_amount=15.99)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        yield order


@pytest.fixture
async def test_other_user_order():
    """Creates an order belonging to a different user to test authorization."""
    async with TestingSessionLocal() as session:
        user2 = User(id=2, email="other@example.com", hashed_password="pw", is_active=True)
        session.add(user2)
        await session.commit()

        order = Order(user_id=2, status=OrderStatusEnum.PENDING, total_amount=20.00)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        yield order


@pytest.mark.asyncio
async def test_unauthorized_users_cannot_access_another_users_order(async_client, test_other_user_order):
    # Attempting to pay for user 2's order while authenticated as user 1
    response = await async_client.post(f"/payments/create-checkout-session/{test_other_user_order.id}")

    assert response.status_code == 400
    assert "Invalid order" in response.json()["detail"]


@pytest.mark.asyncio
@patch("stripe.checkout.Session.create")
async def test_stripe_errors_do_not_expose_internal_details(mock_create, async_client, test_order):
    # Simulate an internal Stripe exception that contains sensitive stack trace or keys
    mock_create.side_effect = stripe.error.StripeError("Sensitive Internal Stripe Failure 999")

    response = await async_client.post(f"/payments/create-checkout-session/{test_order.id}")

    assert response.status_code == 500
    assert "Payment gateway error" in response.json()["detail"]
    assert "Sensitive Internal" not in response.text


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
@patch("stripe.PaymentIntent.retrieve")
async def test_repeated_webhook_events_create_only_one_payment(
        mock_retrieve, mock_construct, async_client, test_order
):
    session_id = "cs_test_idempotent_123"

    mock_construct.return_value = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': session_id,
                'payment_status': 'paid',
                'payment_intent': "pi_test_123",
                'amount_total': 1599,
                'metadata': {'order_id': str(test_order.id), 'user_id': "1"}
            }
        }
    }

    mock_retrieve.return_value.status = "succeeded"
    mock_retrieve.return_value.currency = "usd"
    mock_retrieve.return_value.amount = 1599

    # 1. First webhook call (simulating successful payment)
    response1 = await async_client.post("/payments/webhook", json={}, headers={"stripe-signature": "test"})
    assert response1.status_code == 200

    # 2. Second webhook call (simulating network duplicate/retry from Stripe)
    response2 = await async_client.post("/payments/webhook", json={}, headers={"stripe-signature": "test"})
    assert response2.status_code == 200

    # 3. Explicitly verify the actual database state
    async with TestingSessionLocal() as session:
        db_order = await session.get(Order, test_order.id)
        assert db_order.status == OrderStatusEnum.PAID

        payments = (await session.execute(select(Payment).where(Payment.order_id == test_order.id))).scalars().all()
        assert len(payments) == 1  # Ensures idempotency
        assert payments[0].external_payment_id == session_id


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
@patch("stripe.PaymentIntent.retrieve")
async def test_incorrect_payment_amounts_do_not_mark_order_as_paid(mock_retrieve, mock_construct, async_client,
                                                                   test_order):
    mock_construct.return_value = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': "cs_test_wrong_amount",
                'payment_status': 'paid',
                'payment_intent': "pi_test_123",
                'metadata': {'order_id': str(test_order.id), 'user_id': "1"}
            }
        }
    }

    mock_retrieve.return_value.status = "succeeded"
    mock_retrieve.return_value.currency = "usd"
    mock_retrieve.return_value.amount = 9999  # Bad amount (expected 1599)

    response = await async_client.post("/payments/webhook", json={}, headers={"stripe-signature": "test"})

    assert response.status_code == 400
    assert "amount mismatch" in response.json()["detail"].lower()

    async with TestingSessionLocal() as session:
        db_order = await session.get(Order, test_order.id)
        assert db_order.status == OrderStatusEnum.PENDING  # Must NOT be paid


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
@patch("stripe.PaymentIntent.retrieve")
async def test_invalid_currencies_are_rejected(mock_retrieve, mock_construct, async_client, test_order):
    mock_construct.return_value = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': "cs_test_wrong_currency",
                'payment_status': 'paid',
                'payment_intent': "pi_test_123",
                'amount_total': 1599,
                'metadata': {'order_id': str(test_order.id), 'user_id': "1"}
            }
        }
    }

    mock_retrieve.return_value.status = "succeeded"
    mock_retrieve.return_value.currency = "eur"  # Invalid currency (expected usd)
    mock_retrieve.return_value.amount = 1599

    response = await async_client.post("/payments/webhook", json={}, headers={"stripe-signature": "test"})

    assert response.status_code == 400
    assert "invalid currency" in response.json()["detail"].lower()

    async with TestingSessionLocal() as session:
        db_order = await session.get(Order, test_order.id)
        assert db_order.status == OrderStatusEnum.PENDING


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
async def test_unpaid_stripe_sessions_do_not_confirm_orders(mock_construct, async_client, test_order):
    mock_construct.return_value = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': "cs_test_unpaid",
                'payment_status': 'unpaid',  # Session exists but user hasn't successfully paid yet
                'metadata': {'order_id': str(test_order.id), 'user_id': "1"}
            }
        }
    }

    response = await async_client.post("/payments/webhook", json={}, headers={"stripe-signature": "test"})

    assert response.status_code == 400
    assert "payment not completed" in response.json()["detail"].lower()

    async with TestingSessionLocal() as session:
        db_order = await session.get(Order, test_order.id)
        assert db_order.status == OrderStatusEnum.PENDING
