from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .routers import auth as auth_router
from .routers import allergens as allergens_router
from .routers import menus as menus_router
from .routers import ingest as ingest_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Allergy Menu Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(allergens_router.router)
app.include_router(menus_router.router)
app.include_router(ingest_router.router)

@app.get("/api/health")
def health():
    return {"ok": True}
