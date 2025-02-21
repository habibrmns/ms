from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from .database import get_db
from .models import User, Base
import os

app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

# Pydantic models
class UserCreate(BaseModel):
    mobile_number: str
    name: str
    password: str

class UserLogin(BaseModel):
    mobile_number: str
    password: str

class UserRoleUpdate(BaseModel):
    role: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Create initial admin user
@app.on_event("startup")
def create_admin_user():
    db = next(get_db())
    admin = db.query(User).filter(User.mobile_number == "8877998877").first()
    if not admin:
        hashed_password = get_password_hash("123qwe123qwe")
        admin = User(mobile_number="8877998877", name="Admin", password_hash=hashed_password, role="admin")
        db.add(admin)
        db.commit()

# Endpoints
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.mobile_number == user.mobile_number).first():
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(mobile_number=user.mobile_number, name=user.name, password_hash=hashed_password, role="user")
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.mobile_number == user.mobile_number).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt_token({"sub": str(db_user.id), "role": db_user.role})
    return {"token": token}

@app.get("/users")
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).all()
    return [{"id": u.id, "mobile_number": u.mobile_number, "name": u.name, "role": u.role} for u in users]

@app.patch("/users/{user_id}")
def update_user_role(user_id: int, role_update: UserRoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role_update.role
    db.commit()
    return {"message": "User role updated"}