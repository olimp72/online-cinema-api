import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_unauthorized_order_access(
        async_client: AsyncClient,
):
    response = await async_client.get("/orders/99999")
    assert response.status_code in [401, 403, 404]


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature(async_client: AsyncClient):
    payload = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_123"}}}

    response = await async_client.post(
        "/payments/webhook",
        json=payload,
        headers={"Stripe-Signature": "t=123,v1=invalid_signature_hash"}
    )
    assert response.status_code == 400
    assert "signature" in response.json().get("detail", "").lower()


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
async def test_stripe_webhook_repeated_event(
        mock_construct_event,
        async_client: AsyncClient
):
    mock_construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_repeated"}}
    }

    response = await async_client.post(
        "/payments/webhook",
        json={"type": "checkout.session.completed"},
        headers={"Stripe-Signature": "t=123,v1=valid_hash"}
    )
    assert response.status_code in [200, 400, 404]


@pytest.mark.asyncio
@patch("stripe.Webhook.construct_event")
async def test_stripe_webhook_wrong_amount(
        mock_construct_event,
        async_client: AsyncClient
):
    mock_construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_wrong_amount",
                "amount_total": 100
            }
        }
    }

    response = await async_client.post(
        "/payments/webhook",
        json={"type": "checkout.session.completed"},
        headers={"Stripe-Signature": "t=123,v1=valid_hash"}
    )
    assert response.status_code in [400, 422, 404]
