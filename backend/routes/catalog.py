"""
Catalog routes — TMDB-backed when TMDB_API_KEY is set; otherwise empty results.
Does not host or stream copyrighted video.
"""
from __future__ import annotations

import os
from typing import Optional

import aiohttp
from fastapi import APIRouter, Query

router = APIRouter()

TMDB = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w342"


def _key() -> str:
    return os.getenv("TMDB_API_KEY", "").strip()


async def _tmdb(path: str, params: Optional[dict] = None):
    key = _key()
    if not key:
        return None
    params = dict(params or {})
    params["api_key"] = key
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{TMDB}{path}", params=params, timeout=12) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


def _map_item(item: dict) -> dict:
    media = item.get("media_type") or ("tv" if "first_air_date" in item else "movie")
    title = item.get("title") or item.get("name") or ""
    date = item.get("release_date") or item.get("first_air_date") or ""
    poster = item.get("poster_path")
    return {
        "id": item.get("id"),
        "catalog_id": f"tmdb:{media}:{item.get('id')}",
        "title": title,
        "year": date[:4] if date else "",
        "overview": item.get("overview") or "",
        "poster_url": (IMG + poster) if poster else "",
        "content_type": media,
        "vote_average": item.get("vote_average"),
        "source": "tmdb",
    }


@router.get("/trending")
async def trending():
    data = await _tmdb("/trending/all/day")
    if not data:
        return {"results": [], "note": "Set TMDB_API_KEY for live catalog"}
    results = [_map_item(x) for x in data.get("results", [])[:20]]
    return {"results": results}


@router.get("/search")
async def search(q: str = Query("", min_length=0), page: int = 1):
    q = (q or "").strip()
    if not q:
        return {"results": []}
    data = await _tmdb("/search/multi", {"query": q, "page": page, "include_adult": "false"})
    if not data:
        return {"results": [], "note": "Set TMDB_API_KEY for live catalog"}
    results = [
        _map_item(x)
        for x in data.get("results", [])
        if x.get("media_type") in ("movie", "tv")
    ][:20]
    return {"results": results, "page": page}


@router.get("/{catalog_id}")
async def details(catalog_id: str):
    # catalog_id form: tmdb:movie:123 or bare numeric as movie
    parts = catalog_id.replace("tmdb:", "").split(":")
    if len(parts) == 2:
        media, mid = parts[0], parts[1]
    else:
        media, mid = "movie", parts[0]
    data = await _tmdb(f"/{media}/{mid}")
    if not data:
        return None
    mapped = _map_item({**data, "media_type": media})
    mapped["runtime"] = data.get("runtime") or (data.get("episode_run_time") or [None])[0]
    mapped["genres"] = [g.get("name") for g in data.get("genres") or []]
    return mapped


@router.get("/{catalog_id}/similar")
async def similar(catalog_id: str):
    parts = catalog_id.replace("tmdb:", "").split(":")
    if len(parts) == 2:
        media, mid = parts[0], parts[1]
    else:
        media, mid = "movie", parts[0]
    data = await _tmdb(f"/{media}/{mid}/similar")
    if not data:
        return {"results": []}
    return {"results": [_map_item({**x, "media_type": media}) for x in data.get("results", [])[:12]]}
