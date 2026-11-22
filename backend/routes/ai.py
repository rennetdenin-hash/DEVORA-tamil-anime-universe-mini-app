"""
AI discovery — grounds answers in catalog search first.
Does not invent titles, dates, cast, or ratings.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from routes.catalog import search as catalog_search

router = APIRouter()


class DiscoverBody(BaseModel):
    prompt: str


@router.post("/discover")
async def discover(body: DiscoverBody):
    prompt = (body.prompt or "").strip()
    if not prompt:
        return {"results": [], "message": "Describe what you want to watch."}

    # Phase-1 grounding: use catalog search on the prompt text.
    # Later: parse mood/language/runtime with an LLM, then filter TMDB.
    data = await catalog_search(q=prompt, page=1)
    results = data.get("results") or []
    message = (
        f"Catalog matches for “{prompt}”."
        if results
        else "No grounded catalog matches yet. Try a title, genre, or language keyword."
    )
    return {
        "results": results[:10],
        "message": message,
        "grounded": True,
        "disclaimer": "Factual metadata comes from the catalog provider. Subjective taste is labeled when used.",
    }


@router.post("/compare")
async def compare():
    return {"message": "Compare endpoint placeholder — supply two catalog IDs in a later phase."}


@router.post("/identify")
async def identify():
    return {"message": "Identify endpoint placeholder — ask for remembered details then search catalog."}
