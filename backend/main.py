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
from fastapi.responses import FileResponse

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

# Serve the frontend reliably when deployed from the repository root.
# backend/main.py -> repository root -> frontend/index.html
_project_root = Path(__file__).resolve().parent.parent
_frontend = _project_root / "frontend"
_frontend_enabled = os.getenv("SERVE_FRONTEND", "1") == "1" and _frontend.is_dir()

if _frontend_enabled:
    @app.get("/", include_in_schema=False)
    async def frontend_home():
        index_file = _frontend / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return {"detail": "Frontend index.html not found"}

    # Fallback for frontend files (styles/, scripts/, etc.).
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    async def root_status():
        return {"status": "online", "message": "NOVA Movie Hub API is running", "frontend_available": False}


@app.on_event("startup")
async def startup():
    # Ensure Mongo indexes if configured
    try:
        from database.sessions import ensure_indexes
        await ensure_indexes()
    except Exception as e:
        print(f"[startup] indexes skipped: {e}")
