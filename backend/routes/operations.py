"""
Operation / reward sessions.
Bot creates a session → Mini App opens with start_param=op_<session_id>
→ AdsGram Reward → provider Reward URL or client poll → server marks verified
→ bot delivers file (idempotent).
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter()

# In-memory store for staging. Replace with Mongo (database/sessions.py) in production.
_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _now() -> datetime:
    return datetime.utcnow()


class CreateOperationBody(BaseModel):
    user_id: int
    operation_type: str = Field(default="file_unlock", description="file_unlock | batch_unlock | custom")
    operation_ref: str = Field(..., description="file id / store code / internal ref")
    title: Optional[str] = "Unlock required"
    description: Optional[str] = None
    ttl_minutes: int = 10
    required_ads: int = Field(default=1, ge=1, le=5, description="1 = single file, 3 = send all / selected")
    file_ids: Optional[list] = None
    bot_secret: Optional[str] = None  # shared secret so only your bot can create sessions


class RewardCallbackBody(BaseModel):
    """Optional client notification — never treat as sole proof."""
    session_id: str
    event: str = "client_reward"


def _require_bot_secret(provided: Optional[str]) -> None:
    expected = os.getenv("OPERATION_BOT_SECRET") or os.getenv("BOT_TOKEN")
    if not expected:
        return  # open in pure local dev
    if not provided or provided != expected:
        raise HTTPException(status_code=403, detail="Invalid bot secret")


@router.post("")
async def create_operation(body: CreateOperationBody):
    """Called by the bot when an eligible operation needs a reward step."""
    _require_bot_secret(body.bot_secret)
    session_id = secrets.token_urlsafe(16)
    expires = _now() + timedelta(minutes=max(2, min(body.ttl_minutes, 60)))
    doc = {
        "session_id": session_id,
        "user_id": body.user_id,
        "operation_type": body.operation_type,
        "operation_ref": body.operation_ref,
        "required_ads": int(body.required_ads or 1),
        "ads_completed": 0,
        "file_ids": list(body.file_ids or []),
        "title": body.title or "Unlock required",
        "description": body.description
        or "Watch a short reward ad so the bot can unlock this file. Verification is server-side.",
        "status": "pending",
        "status_label": "Pending",
        "created_at": _now().isoformat() + "Z",
        "expires_at": expires.isoformat() + "Z",
        "verified_at": None,
        "delivered_at": None,
        "idempotency_key": secrets.token_hex(8),
    }
    _SESSIONS[session_id] = doc
    return {
        "session_id": session_id,
        "status": doc["status"],
        "expires_at": doc["expires_at"],
        "required_ads": int(body.required_ads or 1),
        "ads_completed": 0,
        "start_param": f"op_{session_id}",
        "webapp_path": f"?tgWebAppStartParam=op_{session_id}",
    }


@router.get("/{session_id}")
async def get_operation(session_id: str):
    doc = _SESSIONS.get(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    # Expiry
    try:
        exp = datetime.fromisoformat(doc["expires_at"].replace("Z", ""))
        if _now() > exp and doc["status"] not in ("verified", "delivered"):
            doc["status"] = "expired"
            doc["status_label"] = "Expired"
    except Exception:
        pass
    return {
        "session_id": doc["session_id"],
        "status": doc["status"],
        "status_label": doc.get("status_label") or doc["status"],
        "title": doc.get("title"),
        "description": doc.get("description"),
        "operation_type": doc.get("operation_type"),
        "required_ads": int(doc.get("required_ads") or 1),
        "ads_completed": int(doc.get("ads_completed") or 0),
        "file_ids": doc.get("file_ids") or [],
        "expires_at": doc.get("expires_at"),
        "verified_at": doc.get("verified_at"),
        "delivered_at": doc.get("delivered_at"),
    }


@router.post("/{session_id}/mark_verified")
async def mark_verified(
    session_id: str,
    bot_secret: Optional[str] = Query(None),
    x_bot_secret: Optional[str] = Header(None, alias="X-Bot-Secret"),
    userid: Optional[str] = Query(None, description="AdsGram Reward URL [userId] substitute"),
    public: Optional[str] = Query(None, description="1 to allow AdsGram/test without bot secret when enabled"),
):
    """
    Server-side verification entry point.
    - Call from AdsGram Reward URL: .../operations/{session_id}/mark_verified?userid=[userId]
    - Or from your bot after provider confirmation.
    Idempotent: repeated calls do not double-verify.
    """
    secret = bot_secret or x_bot_secret
    # Allow AdsGram / test client without secret if OPERATION_PUBLIC_REWARD=1 or public=1
    if os.getenv("OPERATION_PUBLIC_REWARD", "0") != "1" and str(public or "") != "1":
        _require_bot_secret(secret)

    doc = _SESSIONS.get(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")

    if doc["status"] in ("verified", "delivered", "operation_queued"):
        return {
            "ok": True,
            "status": doc["status"],
            "idempotent": True,
            "required_ads": doc.get("required_ads", 1),
            "ads_completed": doc.get("ads_completed", 0),
        }

    if doc["status"] == "expired":
        raise HTTPException(status_code=410, detail="Session expired")

    # Optional: bind AdsGram userId to session user_id
    if userid:
        try:
            if int(userid) != int(doc["user_id"]):
                raise HTTPException(status_code=403, detail="User mismatch")
        except ValueError:
            pass

    need = int(doc.get("required_ads") or 1)
    done = int(doc.get("ads_completed") or 0) + 1
    doc["ads_completed"] = done
    if done < need:
        doc["status"] = "pending"
        doc["status_label"] = f"Ad {done}/{need} done — watch the next"
        return {
            "ok": True,
            "status": "pending",
            "session_id": session_id,
            "required_ads": need,
            "ads_completed": done,
            "complete": False,
        }

    doc["status"] = "verified"
    doc["status_label"] = "Verified"
    doc["verified_at"] = _now().isoformat() + "Z"
    return {
        "ok": True,
        "status": "verified",
        "session_id": session_id,
        "required_ads": need,
        "ads_completed": done,
        "complete": True,
    }


@router.post("/{session_id}/mark_delivered")
async def mark_delivered(
    session_id: str,
    bot_secret: Optional[str] = Query(None),
    x_bot_secret: Optional[str] = Header(None, alias="X-Bot-Secret"),
):
    """Bot calls after successful file delivery (idempotent)."""
    _require_bot_secret(bot_secret or x_bot_secret)
    doc = _SESSIONS.get(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    if doc["status"] == "delivered":
        return {"ok": True, "status": "delivered", "idempotent": True}
    if doc["status"] not in ("verified", "operation_queued"):
        raise HTTPException(status_code=409, detail=f"Cannot deliver from status={doc['status']}")
    doc["status"] = "delivered"
    doc["status_label"] = "Delivered"
    doc["delivered_at"] = _now().isoformat() + "Z"
    return {"ok": True, "status": "delivered"}


@router.get("/pending/{user_id}")
async def list_pending(user_id: int, bot_secret: Optional[str] = Query(None)):
    """Bot helper: list open sessions for a user."""
    _require_bot_secret(bot_secret)
    out = [
        s for s in _SESSIONS.values()
        if s.get("user_id") == user_id and s.get("status") in ("pending", "verified", "operation_queued")
    ]
    return {"items": out}
