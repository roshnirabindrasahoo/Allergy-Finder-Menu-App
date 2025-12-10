from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# app/main.py
from sqlalchemy import text
from fastapi import Depends
from .db import get_db

# Ensure models are registered on Base.metadata
from . import models  # <-- add this line

# Routers
from .routers import auth as auth_router
from .routers import allergens as allergens_router
from .routers import ingest as ingest_router
from .routers import menus as menus_router

# DB bootstrap
from .db import Base, engine

# Base.metadata.create_all(bind=engine)


app = FastAPI(title="Allergy Menu Finder")

# ---- CORS: allow your frontend in dev (Vite 5173, Next 3000) ----
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "https://allergy-finder-menu-app.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    # Option A: simple message
    return JSONResponse({"message": "Allergy Menu Finder API. See /docs for Swagger."})

# ---- Health ----
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/health/db")
def db_health(db=Depends(get_db)):
    who = db.execute(text("SELECT current_user")).scalar()
    return {"db": "ok", "current_user": who}


# ---- Mount routers ----
app.include_router(auth_router.router)
app.include_router(allergens_router.router)
app.include_router(ingest_router.router)
app.include_router(menus_router.router)
