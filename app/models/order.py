import enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING, nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    user = relationship("User", backref="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    price_at_order = Column(DECIMAL(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    movie = relationship("Movie")
