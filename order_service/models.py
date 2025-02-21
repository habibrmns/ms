from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Cart(Base):
    __tablename__ = "cart"
    __table_args__ = {"schema": "order"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "order"}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    status = Column(Enum("pending", "completed", name="status_enum"), default="pending")
    created_at = Column(DateTime, nullable=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = {"schema": "order"}
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.orders.id"), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)