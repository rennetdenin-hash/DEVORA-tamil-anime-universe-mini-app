"""
NOVA Movie Hub — FastAPI backend
Run from the backend directory: uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir.parent / ".env")
load_dotenv(_backend_dir / ".env")
load_dotenv()

from routes import auth, catalog, operations, watchlist, ai, health  # noqa: E402

app = FastAPI(
    title="NOVA Movie Hub API",
    version="0.1.0",
    description="Catalog + AI discovery + operation/reward sessions for Telegram Mini App",
)

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

# Keep the original repository layout: frontend/ beside backend/.
# FRONTEND_DIR may be set in the hosting environment to an absolute directory.
_candidates = []
_configured = os.getenv("FRONTEND_DIR")
if _configured:
    _candidates.append(Path(_configured))
_candidates.extend([
    _backend_dir.parent / "frontend",
    _backend_dir / "frontend",
    Path.cwd() / "frontend",
    Path.cwd().parent / "frontend",
    Path("/app/frontend"),
    Path("/workspace/frontend"),
    Path("/opt/app/frontend"),
])

_frontend = next(
    (p.resolve() for p in _candidates if (p / "index.html").is_file()),
    None,
)
_frontend_enabled = os.getenv("SERVE_FRONTEND", "1") == "1" and _frontend is not None

if _frontend_enabled:
    @app.get("/", include_in_schema=False)
    async def frontend_home():
        return FileResponse(_frontend / "index.html")

    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    async def root_status():
        return {
            "status": "online",
            "message": "NOVA Movie Hub API is running",
            "frontend_available": False,
            "backend_dir": str(_backend_dir),
            "working_dir": str(Path.cwd()),
            "frontend_candidates_checked": [str(p.resolve()) for p in _candidates],
            "frontend_dir_env_set": bool(_configured),
        }

@app.on_event("startup")
async def startup():
    try:
        from database.sessions import ensure_indexes
        await ensure_indexes()
    except Exception as e:
        print(f"[startup] indexes skipped: {e}")
