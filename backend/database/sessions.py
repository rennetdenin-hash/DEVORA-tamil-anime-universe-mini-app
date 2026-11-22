"""
Mongo-backed operation sessions (optional).
Operations route currently uses in-memory store for easy staging.
Wire this module when MONGO_URI is set.
"""
from __future__ import annotations

import os
from typing import Any, Optional

_client = None
_col = None


async def ensure_indexes():
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        return
    global _client, _col
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(uri)
        db_name = os.getenv("MONGO_DB", "nova_movie_hub")
        _col = _client[db_name]["operation_sessions"]
        await _col.create_index("session_id", unique=True)
        await _col.create_index([("user_id", 1), ("status", 1)])
        await _col.create_index("expires_at", expireAfterSeconds=0)  # optional TTL if field is a date
    except Exception as e:
        print(f"sessions ensure_indexes: {e}")


async def save_session(doc: dict) -> None:
    if _col is None:
        return
    await _col.update_one({"session_id": doc["session_id"]}, {"$set": doc}, upsert=True)


async def get_session(session_id: str) -> Optional[dict]:
    if _col is None:
        return None
    return await _col.find_one({"session_id": session_id}, {"_id": 0})
