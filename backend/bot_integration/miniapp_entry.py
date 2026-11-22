"""
Drop-in helpers for the existing Pyrogram bot.
Prefer utils/ad_gate.py in the bot package (same API).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Sequence

import aiohttp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def miniapp_url() -> str:
    return (os.getenv("MINIAPP_URL") or "").rstrip("/")


def api_url() -> str:
    return (os.getenv("NOVA_API_URL") or "").rstrip("/")


def bot_secret() -> str:
    return os.getenv("OPERATION_BOT_SECRET") or os.getenv("BOT_TOKEN") or ""


async def create_unlock_session(
    user_id: int,
    operation_ref: str,
    *,
    title: str = "Unlock file",
    description: Optional[str] = None,
    operation_type: str = "file_unlock",
    required_ads: int = 1,
    file_ids: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, Any]]:
    base = api_url()
    if not base:
        return None
    payload = {
        "user_id": user_id,
        "operation_type": operation_type,
        "operation_ref": str(operation_ref),
        "title": title,
        "description": description
        or f"Complete {required_ads} reward ad(s). Verified on the server.",
        "ttl_minutes": 15,
        "required_ads": int(max(1, min(required_ads, 5))),
        "file_ids": list(file_ids or []),
        "bot_secret": bot_secret(),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base}/operations", json=payload, timeout=15) as resp:
                if resp.status >= 400:
                    return None
                return await resp.json()
    except Exception:
        return None


def unlock_keyboard(session: Dict[str, Any]) -> Optional[InlineKeyboardMarkup]:
    url = miniapp_url()
    if not url or not session:
        return None
    start = session.get("start_param") or f"op_{session.get('session_id')}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Open unlock", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(
            "Open Mini App",
            url=f"https://t.me/{os.getenv('BOT_USERNAME', 'YourBot')}?startapp={start}",
        )],
    ])


async def is_session_verified(session_id: str) -> bool:
    base = api_url()
    if not base or not session_id:
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base}/operations/{session_id}", timeout=12) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                return (data.get("status") or "").lower() in ("verified", "delivered", "operation_queued")
    except Exception:
        return False


async def mark_delivered(session_id: str) -> bool:
    base = api_url()
    if not base or not session_id:
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base}/operations/{session_id}/mark_delivered",
                params={"bot_secret": bot_secret()},
                timeout=12,
            ) as resp:
                return resp.status < 400
    except Exception:
        return False
