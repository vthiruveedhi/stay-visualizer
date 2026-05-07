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
        prompt="A group of {guests} friends laughing by the pool, golden-hour light, candid",
        image="https://images.unsplash.com/photo-1530653333484-8e6c1ee8d4ee?auto=format&fit=crop&w=600&q=70",
        keywords=("pool", "swim", "swimming", "splash", "water"),
    ),
    Scene(
        key="bedroom",
        label="Cozy in the bedroom",
        prompt="A couple relaxing on the bed, warm bedside lighting, magazines and coffee",
        image="https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=600&q=70",
        keywords=("bedroom", "bed", "sleep", "relax", "morning", "coffee"),
    ),
    Scene(
        key="dining",
        label="Family dinner",
        prompt="A large family eating dinner at a long wooden table, candles, festive food",
        image="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=600&q=70",
        keywords=("dining", "dinner", "lunch", "food", "eat", "table", "feast"),
    ),
    Scene(
        key="hall",
        label="Movie night in the hall",
        prompt="A group of friends on a sofa watching a movie, popcorn, dim cozy lighting",
        image="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=600&q=70",
        keywords=("hall", "living", "sofa", "movie", "tv", "couch", "lounge"),
    ),
    Scene(
        key="garden",
        label="Lawn party",
        prompt="A group celebrating outdoors on a green lawn, fairy lights, evening",
        image="https://images.unsplash.com/photo-1530023367847-a683933f4172?auto=format&fit=crop&w=600&q=70",
        keywords=("lawn", "garden", "outdoor", "outside", "party", "evening"),
    ),
    Scene(
        key="bbq",
        label="BBQ night",
        prompt="Friends grilling at a BBQ, smoke rising, drinks in hand, warm dusk light",
        image="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=70",
        keywords=("bbq", "grill", "barbecue", "cook"),
    ),
]


# Generic fallback when nothing matches.
_FALLBACK = Scene(
    key="generic",
    label="People enjoying the stay",
    prompt="A happy group of {guests} people enjoying their stay, warm lighting, candid",
    image="https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=600&q=70",
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
