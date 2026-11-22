"""
NOVA Movie Hub — FastAPI backend
Run: uvicorn main:app --host 0.0.0.0 --port 8081 --reload
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

from routes import auth, catalog, operations, watchlist, ai, health  # noqa: E402

app = FastAPI(
    title="NOVA Movie Hub API",
    version="0.1.0",
    description="Catalog + AI discovery + operation/reward sessions for Telegram Mini App",
)

# Restrict CORS in production to your Mini App origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
app.include_router(operations.router, prefix="/operations", tags=["operations"])

# Optional: serve frontend from same process in staging
_frontend = Path(__file__).resolve().parent.parent / "frontend"
if _frontend.is_dir() and os.getenv("SERVE_FRONTEND", "1") == "1":
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")


@app.on_event("startup")
async def startup():
    # Ensure Mongo indexes if configured
    try:
        from database.sessions import ensure_indexes
        await ensure_indexes()
    except Exception as e:
        print(f"[startup] indexes skipped: {e}")
