"""
Telegram Mini App initData validation (HMAC-SHA256).
Never trust user_id from the client without verifying initData.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl


def _bot_token() -> str:
    return os.getenv("BOT_TOKEN", "").strip()


def validate_init_data(init_data: str, max_age_sec: int = 86400) -> Optional[Dict[str, Any]]:
    """
    Validate Telegram WebApp initData.
    Returns parsed user dict on success, None on failure.
    """
    if not init_data or not _bot_token():
        return None

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    # Data-check-string: sorted key=value joined by \n
    check_list = [f"{k}={v}" for k, v in sorted(pairs.items())]
    data_check_string = "\n".join(check_list)

    secret_key = hmac.new(
        b"WebAppData",
        _bot_token().encode(),
        hashlib.sha256,
    ).digest()
    calculated = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        return None

    # Optional auth_date freshness
    try:
        auth_date = int(pairs.get("auth_date") or 0)
        if auth_date and (time.time() - auth_date) > max_age_sec:
            return None
    except (TypeError, ValueError):
        pass

    user = None
    if pairs.get("user"):
        try:
            user = json.loads(pairs["user"])
        except Exception:
            user = None

    return {
        "user": user,
        "auth_date": pairs.get("auth_date"),
        "query_id": pairs.get("query_id"),
        "start_param": pairs.get("start_param"),
        "raw": pairs,
    }
