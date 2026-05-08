"""ComfyUI integration via the upstream multipart wrapper.

The upstream `/run` endpoint accepts:
    multipart/form-data
        image  (file)   - reference image
        prompt (text)   - what to render

…and responds with the generated PNG bytes directly.

We:
  1. Match the user's prompt to a curated scene (safety + decent default).
  2. Download the property's reference image.
  3. POST it + the (scene + user) prompt to the upstream.
  4. Save the returned PNG under static/generated/ so the browser can fetch it.
  5. Return its public URL to the frontend.

If `COMFYUI_ENDPOINT` is empty, or the upstream call fails, we fall back to
the mock generator so the demo never breaks during a vendor pitch.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path

import httpx

from app.config import settings
from app.scenes import Scene, match_scene

logger = logging.getLogger("comfy")

# Skip the ngrok-free interstitial warning for programmatic requests.
_NGROK_SKIP = {"ngrok-skip-browser-warning": "1"}


async def generate_image(
    prompt: str,
    guests: int = 4,
    reference_image: str | None = None,
) -> dict:
    """Public entrypoint. Auto-falls-back to mock on failure."""
    scene = match_scene(prompt)
    if settings.comfyui_endpoint:
        try:
            return await generate_via_comfyui(scene, prompt, guests, reference_image)
        except Exception as e:
            logger.warning("ComfyUI call failed (%s); falling back to mock", e)
    return await generate_mock(scene, prompt, guests)


# ---------------------------------------------------------------------------
# Mock — used when the upstream is unconfigured or unreachable.
# ---------------------------------------------------------------------------

async def generate_mock(scene: Scene, prompt: str, guests: int) -> dict:
    await asyncio.sleep(settings.mock_delay_seconds)
    return {
        "image_url": scene.image,
        "caption": scene.prompt.format(guests=guests),
        "scene_key": scene.key,
        "source": "mock",
    }


# ---------------------------------------------------------------------------
# Real call.
# ---------------------------------------------------------------------------

async def generate_via_comfyui(
    scene: Scene,
    prompt: str,
    guests: int,
    reference_image: str | None,
) -> dict:
    ref_url = reference_image or settings.default_reference_image
    full_prompt = _build_prompt(scene, prompt, guests)

    cache_key = _hash(ref_url, full_prompt)
    out_path = settings.generated_dir / f"{cache_key}.png"

    if out_path.exists():
        return {
            "image_url": f"/static/generated/{out_path.name}",
            "caption": full_prompt,
            "scene_key": scene.key,
            "source": "comfyui-cache",
        }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0)) as client:
        # 1) Pull the reference image.
        ref = await client.get(ref_url, headers=_NGROK_SKIP)
        ref.raise_for_status()
        image_bytes = ref.content
        content_type = ref.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
        filename = f"reference.{ext}"

        # 2) POST to the wrapper.
        files = {"image": (filename, image_bytes, content_type)}
        data = {"prompt": full_prompt}
        gen = await client.post(
            settings.comfyui_endpoint,
            files=files,
            data=data,
            headers=_NGROK_SKIP,
        )
        gen.raise_for_status()

        out_ctype = gen.headers.get("content-type", "")
        if not out_ctype.startswith("image/"):
            # Wrapper sometimes returns JSON errors; surface them clearly.
            preview = gen.text[:300]
            raise RuntimeError(f"upstream returned {out_ctype!r}: {preview}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(gen.content)

    return {
        "image_url": f"/static/generated/{out_path.name}",
        "caption": full_prompt,
        "scene_key": scene.key,
        "source": "comfyui",
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _build_prompt(scene: Scene, user_prompt: str, guests: int) -> str:
    """Compose the prompt sent to Flux Kontext.

    Strategy:
      - Subject = the user's words (or the curated scene template if those
        are missing). Describes ONLY the people to be added.
      - No atmosphere/lighting/decoration cues — Flux Kontext will otherwise
        invent string lights, candles, plants, etc. that aren't in the
        property photo.
      - A strict preservation clause is appended that explicitly forbids
        adding new objects or changing the room.
    """
    user_text = user_prompt.strip().rstrip(".")
    if not user_text:
        user_text = scene.prompt.format(guests=guests).rstrip(".")

    return (
        f"Add to the scene: {user_text}. "
        f"Strict preservation: keep the room exactly as in the reference — "
        f"the same walls, floor, ceiling, furniture, doors, windows, "
        f"existing light fixtures, plants, and decor. "
        f"Do not add string lights, fairy lights, candles, balloons, "
        f"festoons, extra furniture, or any decoration. "
        f"Match the original lighting and color tone. "
        f"Only insert the people described, naturally placed in the scene."
    )


def _hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:16]
