"""FastAPI entrypoint.

Serves the demo property page + `/api/*` endpoints used by the AI tab.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.comfy import generate_image
from app.scenes import suggested_scenes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="stay-visualizer")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/suggestions")
def suggestions(property_id: str = "default"):
    """Pre-curated scenes shown when the AI tab is opened."""
    return {
        "property_id": property_id,
        "suggestions": [
            {
                "key": s.key,
                "label": s.label,
                "image_url": s.image,
                "prompt": s.prompt.format(guests=4),
            }
            for s in suggested_scenes(limit=4)
        ],
    }


class GenerateRequest(BaseModel):
    property_id: str = "default"
    prompt: str = Field(..., min_length=2, max_length=200)
    guests: int = Field(4, ge=1, le=50)


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    return await generate_image(
        prompt=req.prompt,
        guests=req.guests,
    )
