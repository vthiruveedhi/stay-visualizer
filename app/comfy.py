"""ComfyUI integration.

Currently stubbed: returns the preset image for the matched scene after a small
delay. When `settings.comfyui_url` is set, swap `generate_image()` to use
`generate_via_comfyui()` (skeleton below — finish once the workflow JSON and
ComfyUI URL are available).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path

import httpx

from app.config import settings
from app.scenes import Scene, match_scene

logger = logging.getLogger("comfy")


async def generate_image(prompt: str, guests: int = 4, reference_image: str | None = None) -> dict:
    """Public entrypoint. Switches to real ComfyUI once configured."""
    scene = match_scene(prompt)
    if settings.comfyui_url:
        try:
            return await generate_via_comfyui(scene, prompt, guests, reference_image)
        except Exception as e:
            logger.exception("ComfyUI call failed, falling back to mock: %s", e)
    return await generate_mock(scene, prompt, guests)


# ---------------------------------------------------------------------------
# Mock implementation — used until ComfyUI is wired up.
# ---------------------------------------------------------------------------

async def generate_mock(scene: Scene, prompt: str, guests: int) -> dict:
    await asyncio.sleep(settings.mock_delay_seconds)
    caption = scene.prompt.format(guests=guests)
    return {
        "image_url": scene.image,
        "caption": caption,
        "scene_key": scene.key,
        "source": "mock",
    }


# ---------------------------------------------------------------------------
# Real implementation skeleton.
#
# ComfyUI's HTTP API:
#   POST /prompt        { "prompt": <workflow_json>, "client_id": <uuid> }
#                       → { "prompt_id": "..." }
#   GET  /history/<id>  → { "<id>": { "outputs": { "<node>": { "images": [...] } } } }
#   GET  /view?filename=...&subfolder=...&type=output  → PNG bytes
#
# Plus a websocket at /ws?clientId=<uuid> for live progress events.
#
# Steps below for when the workflow JSON is in `workflows/flux_kontext.json`:
#   1. Read template, find LoadImage node and replace its `image` input with our
#      reference image filename. (Upload via POST /upload/image first.)
#   2. Find the prompt CLIPTextEncode node, replace `text` with our prompt.
#   3. Replace the KSampler `seed` for variety.
#   4. POST /prompt with the modified workflow.
#   5. Poll /history/<prompt_id> until the output node has an image entry.
#   6. Fetch the PNG via /view, save somewhere, return its public URL.
# ---------------------------------------------------------------------------

async def generate_via_comfyui(
    scene: Scene,
    prompt: str,
    guests: int,
    reference_image: str | None,
) -> dict:
    base = settings.comfyui_url.rstrip("/")
    workflow = _load_workflow()
    full_prompt = scene.prompt.format(guests=guests) + ". " + prompt

    # TODO: parameterize the workflow JSON. Placeholder names below — replace
    # with your actual node ids after dropping in workflows/flux_kontext.json.
    _set_node_input(workflow, node_title="UserPrompt", key="text", value=full_prompt)
    if reference_image:
        _set_node_input(workflow, node_title="ReferenceImage", key="image", value=reference_image)

    client_id = str(uuid.uuid4())
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{base}/prompt", json={"prompt": workflow, "client_id": client_id})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]

        # Poll history. Could be replaced with the websocket for lower latency.
        for _ in range(120):
            h = await client.get(f"{base}/history/{prompt_id}")
            h.raise_for_status()
            data = h.json().get(prompt_id) or {}
            if data.get("outputs"):
                for node_out in data["outputs"].values():
                    for img in node_out.get("images", []):
                        url = (
                            f"{base}/view?filename={img['filename']}"
                            f"&subfolder={img.get('subfolder', '')}"
                            f"&type={img.get('type', 'output')}"
                        )
                        return {
                            "image_url": url,
                            "caption": full_prompt,
                            "scene_key": scene.key,
                            "source": "comfyui",
                        }
            await asyncio.sleep(1)

    raise TimeoutError("ComfyUI did not produce an image within 120s")


def _load_workflow() -> dict:
    path = Path(settings.comfyui_workflow_path)
    if not path.exists():
        raise FileNotFoundError(
            f"workflow JSON not found at {path}. Export from ComfyUI via "
            f"'Save (API Format)' and drop it in."
        )
    return json.loads(path.read_text())


def _set_node_input(workflow: dict, node_title: str, key: str, value) -> None:
    """Find a node by its `_meta.title` (set in ComfyUI) and patch one input."""
    for node in workflow.values():
        if node.get("_meta", {}).get("title") == node_title:
            node.setdefault("inputs", {})[key] = value
            return
    raise KeyError(f"node titled {node_title!r} not found in workflow")
