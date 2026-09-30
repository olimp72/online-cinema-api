from pydantic import BaseModel
from datetime import datetime
from typing import List
from decimal import Decimal
from app.models.order import OrderStatusEnum
from app.schemas.movie import MovieResponse


class OrderItemResponse(BaseModel):
    id: int
    movie: MovieResponse
    price_at_order: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
