"""Scene preset library.

Each preset is a (key, label, prompt, image) tuple where:
  - key:     stable id used by the frontend
  - label:   short text shown on the suggestion card
  - prompt:  ComfyUI text prompt template; {guests} is substituted at request time
  - image:   placeholder/preview image. Replaced by ComfyUI output once wired up.

Keywords below feed `match_scene()` — when a free-text user prompt mentions one
of these words, we serve the associated preset. This is the cheap MVP standin
for the real ComfyUI workflow.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scene:
    key: str
    label: str
    prompt: str
    image: str
    keywords: tuple[str, ...]


# Curated Unsplash photos — themed "people enjoying" stand-ins for the demo.
# These are credible enough for a vendor pitch; swap in real Flux Kontext
# outputs once the workflow is connected.
SCENES: list[Scene] = [
    # Prompts describe ONLY the people (subject). All atmosphere /
    # lighting / decoration cues are deliberately omitted — Flux Kontext
    # will otherwise add string lights, candles, etc. that aren't in the
    # property photo. The preservation clause appended in
    # `comfy._build_prompt()` does the heavy lifting.
    Scene(
        key="pool",
        label="Pool day with friends",
        prompt="{guests} friends standing in the pool, smiling",
        image="/static/property-images/pool-evening.jpg",
        keywords=("pool", "swim", "swimming", "splash"),
    ),
    Scene(
        key="bedroom",
        label="Morning in the bedroom",
        prompt="A couple sitting on the bed having coffee",
        image="/static/property-images/bedroom.jpg",
        keywords=("bedroom", "bed", "sleep"),
    ),
    Scene(
        key="hall",
        label="Hanging out in the hall",
        prompt="A group of friends sitting on the sofa",
        image="/static/property-images/hall.jpg",
        keywords=("hall", "living", "sofa", "movie", "couch", "lounge"),
    ),
    Scene(
        key="dining",
        label="Family dinner",
        prompt="A family of {guests} sitting around the dining table eating",
        image="/static/property-images/dining.jpg",
        # Note: "table" alone is too generic (matches "patio table" etc.)
        # so it's intentionally absent.
        keywords=("dining", "dinner", "lunch", "feast", "eat", "kitchen", "cook"),
    ),
    Scene(
        key="patio",
        label="On the patio",
        prompt="Two couples sitting at the patio table chatting",
        image="/static/property-images/patio.jpg",
        keywords=("patio", "balcony", "veranda", "terrace"),
    ),
    Scene(
        key="garden",
        label="On the lawn",
        prompt="A group of {guests} people standing on the lawn",
        image="/static/property-images/garden.jpg",
        keywords=("lawn", "garden", "outdoor", "outside", "bbq", "grill", "barbecue"),
    ),
]


# Generic fallback when nothing matches. Reuses the hero (pool) image so the
# Flux Kontext reference is always a real property photo.
_FALLBACK = Scene(
    key="generic",
    label="People enjoying the stay",
    prompt="A happy group of {guests} people enjoying their stay, warm lighting, candid",
    image="/static/property-images/pool-evening.jpg",
    keywords=(),
)


def match_scene(prompt: str) -> Scene:
    """Match a free-text prompt to a preset by keyword. Falls back to generic."""
    p = prompt.lower()
    for s in SCENES:
        if any(k in p for k in s.keywords):
            return s
    return _FALLBACK


def suggested_scenes(limit: int = 4) -> list[Scene]:
    return SCENES[:limit]
