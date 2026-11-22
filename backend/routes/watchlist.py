"""Watchlist — in-memory staging. Replace with Mongo in production."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# user_id -> list of items
_STORE: Dict[int, List[dict]] = {}


class AddBody(BaseModel):
    catalog_id: str
    content_type: str = "movie"
    user_id: int = 0  # staging; production uses auth token


@router.get("")
async def list_watchlist(user_id: int = 0):
    return {"items": _STORE.get(user_id, [])}


@router.post("")
async def add_item(body: AddBody):
    uid = body.user_id
    items = _STORE.setdefault(uid, [])
    if any(i.get("catalog_id") == body.catalog_id for i in items):
        return {"ok": True, "duplicate": True}
    item = {
        "id": f"{uid}_{body.catalog_id}",
        "catalog_id": body.catalog_id,
        "content_type": body.content_type,
        "saved_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    return {"ok": True, "item": item}


@router.delete("/{item_id}")
async def remove_item(item_id: str, user_id: int = 0):
    items = _STORE.get(user_id, [])
    new = [i for i in items if i.get("id") != item_id]
    if len(new) == len(items):
        raise HTTPException(status_code=404, detail="Not found")
    _STORE[user_id] = new
    return {"ok": True}
