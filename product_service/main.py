from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from .database import get_db
from .models import Product, Base
from fastapi.staticfiles import StaticFiles
from jose import jwt
import os

app = FastAPI()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# Mount static files for images
app.mount("/images", StaticFiles(directory="images"), name="images")

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str

# Authentication dependency
def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Endpoints
@app.post("/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    new_product = Product(**product.dict(), created_at=datetime.now())
    db.add(new_product)
    db.commit()
    return {"message": "Product created", "product_id": new_product.id}

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "price": p.price, "stock": p.stock, 
             "image_url": p.image_url, "category": p.category, "created_at": p.created_at} for p in products]

@app.get("/products/new")
def get_new_products(db: Session = Depends(get_db)):
    seven_days_ago = datetime.now() - timedelta(days=7)
    new_products = db.query(Product).filter(Product.created_at >= seven_days_ago).all()
    return [{"id": p.id, "name": p.name, "price": p.price, "image_url": p.image_url} for p in new_products]

@app.post("/products/{product_id}/upload-image")
async def upload_image(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    file_path = f"images/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    product.image_url = f"/products/images/{file.filename}"
    db.commit()
    return {"message": "Image uploaded"}

@app.post("/products/{product_id}/decrease-stock")
def decrease_stock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    product.stock -= quantity
    db.commit()
    return {"message": "Stock updated"}