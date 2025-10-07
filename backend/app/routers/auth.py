from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import User
from ..schemas import UserCreate, UserLogin, TokenOut
from ..auth import hash_password, verify_password, create_token

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in ("customer","restaurant","admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    u = User(name=payload.name, email=payload.email,
             password_hash=hash_password(payload.password), role=payload.role)
    db.add(u); db.commit(); db.refresh(u)
    token = create_token({"id": u.id, "email": u.email, "role": u.role})
    return {"token": token}

@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == payload.email).first()
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"id": u.id, "email": u.email, "role": u.role})
    return {"token": token}
