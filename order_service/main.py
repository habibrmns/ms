from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from .database import get_db
from .models import Cart, Order, OrderItem, Base
from jose import jwt
import httpx
import os

app = FastAPI()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# Pydantic models
class CartAdd(BaseModel):
    product_id: int
    quantity: int

# Authentication dependency
def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Endpoints
@app.post("/cart/add")
def add_to_cart(cart: CartAdd, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    user_id = int(token["sub"])
    cart_item = db.query(Cart).filter(Cart.user_id == user_id, Cart.product_id == cart.product_id).first()
    if cart_item:
        cart_item.quantity += cart.quantity
    else:
        cart_item = Cart(user_id=user_id, product_id=cart.product_id, quantity=cart.quantity)
        db.add(cart_item)
    db.commit()
    return {"message": "Added to cart"}

@app.get("/cart")
def get_cart(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    user_id = int(token["sub"])
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    return [{"product_id": item.product_id, "quantity": item.quantity} for item in cart_items]

@app.post("/checkout")
async def checkout(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    user_id = int(token["sub"])
    cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Check stock and update
    async with httpx.AsyncClient() as client:
        for item in cart_items:
            response = await client.post(f"http://localhost:8002/products/{item.product_id}/decrease-stock", json={"quantity": item.quantity})
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Stock issue")
    
    # Create order
    order = Order(user_id=user_id, status="pending", created_at=datetime.now())
    db.add(order)
    db.commit()
    for item in cart_items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    db.commit()
    return {"message": "Order placed"}

@app.get("/orders")
def get_orders(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    user_id = int(token["sub"])
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return [{"id": o.id, "status": o.status, "created_at": o.created_at} for o in orders]

@app.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    user_id = int(token["sub"])
    top_products = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("total_quantity"))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    return [{"product_id": p[0], "total_quantity": p[1]} for p in top_products]