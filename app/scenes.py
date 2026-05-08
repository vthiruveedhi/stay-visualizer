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
    Scene(
        key="pool",
        label="Pool day with friends",
        prompt="{guests} friends laughing by the pool, candid, evening light",
        image="/static/property-images/pool-evening.jpg",
        keywords=("pool", "swim", "swimming", "splash", "water"),
    ),
    Scene(
        key="bedroom",
        label="Cozy in the bedroom",
        prompt="A couple relaxing on the bed, warm light, magazines and coffee",
        image="/static/property-images/bedroom.jpg",
        keywords=("bedroom", "bed", "sleep", "relax", "morning", "coffee"),
    ),
    Scene(
        key="hall",
        label="Movie night in the hall",
        prompt="A group of friends on the sofa watching a movie, popcorn, dim cozy lighting",
        image="/static/property-images/hall.jpg",
        keywords=("hall", "living", "sofa", "movie", "tv", "couch", "lounge"),
    ),
    Scene(
        key="dining",
        label="Family dinner",
        prompt="A family eating dinner around the table, festive, warm light",
        image="/static/property-images/dining.jpg",
        keywords=("dining", "dinner", "lunch", "food", "eat", "table", "feast", "kitchen", "cook"),
    ),
    Scene(
        key="patio",
        label="Evening on the patio",
        prompt="Two couples chatting at a small table on the patio, evening, warm overhead lights",
        image="/static/property-images/patio.jpg",
        keywords=("patio", "balcony", "veranda", "terrace"),
    ),
    Scene(
        key="garden",
        label="Lawn party",
        prompt="A group celebrating outdoors on the lawn at dusk, fairy lights",
        image="/static/property-images/garden.jpg",
        keywords=("lawn", "garden", "outdoor", "outside", "party", "evening", "bbq", "grill", "barbecue"),
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
