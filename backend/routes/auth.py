from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from security.authentication import validate_init_data

router = APIRouter()


class TelegramAuthBody(BaseModel):
    init_data: str


@router.post("/telegram")
async def auth_telegram(body: TelegramAuthBody):
    """
    Validate Telegram WebApp initData and return a short-lived session token.
    Production: replace simple token with signed JWT (BOT_TOKEN as secret is a starting point).
    """
    parsed = validate_init_data(body.init_data)
    if not parsed or not parsed.get("user"):
        raise HTTPException(status_code=401, detail="Invalid Telegram authentication")

    user = parsed["user"]
    uid = user.get("id")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing user id")

    # Lightweight opaque token for staging (replace with JWT in production)
    secret = os.getenv("API_SESSION_SECRET") or os.getenv("BOT_TOKEN") or "dev-secret"
    token = f"nova_{uid}_{int(time.time())}"

    return {
        "ok": True,
        "token": token,
        "user": {
            "id": uid,
            "first_name": user.get("first_name"),
            "username": user.get("username"),
            "language_code": user.get("language_code"),
        },
        "expires_in": 3600,
        "note": "Staging token. Use signed JWT in production.",
    }
