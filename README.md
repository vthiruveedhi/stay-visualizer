# stay-visualizer

MVP demo: a property-detail page with an **AI tab** that shows AI-generated
visuals of "people enjoying" the listed property. Built so a vendor can see
the experience end-to-end before the real ComfyUI / Flux Kontext pipeline is
wired up.

## What's in the box

- A simplified replica of a property listing page (title, stats, tab bar,
  About / Amenities / Reviews etc., booking sidebar)
- A new **AI ✨** tab containing:
  - 4 pre-curated "scene" cards (pool, bedroom, dining, hall, …) — click
    one to drop it into the chat
  - A chat box where users describe a scene in their own words
  - The "generated" image streams back into the chat
- A FastAPI backend with a mock generator that returns curated stock photos
  matched to keywords in the prompt. The same endpoint will call ComfyUI
  once the workflow + URL are dropped in.

The intent is for this to look like a real product to a vendor _today_, while
having a clean seam for swapping in the real Flux Kontext output later.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000>. Click the **AI ✨** tab.

Or with Docker:

```bash
docker build -t stay-visualizer .
docker run --rm -p 8000:8000 stay-visualizer
```

## Wiring up real ComfyUI

Two things to provide:

1. The ComfyUI server URL → set `COMFYUI_URL` in `.env`.
2. The Flux Kontext workflow JSON, exported from ComfyUI via
   **Save (API Format)** → drop at `workflows/flux_kontext.json`.

Then in `app/comfy.py`, finish `generate_via_comfyui()`:
- Replace the placeholder node titles (`UserPrompt`, `ReferenceImage`) with
  the actual `_meta.title` values from your workflow nodes (or look them up by
  `class_type`).
- Confirm the property reference image is uploaded via `POST /upload/image`
  before submitting the prompt (workflow expects a filename, not a URL).

`generate_image()` in `app/comfy.py` already auto-falls-back to the mock if
`COMFYUI_URL` is empty or the call fails — so the demo never breaks.

## Project layout

```
stay-visualizer/
├── app/
│   ├── main.py        # FastAPI app + /api/* endpoints
│   ├── comfy.py       # ComfyUI client (mock + real skeleton)
│   ├── scenes.py      # Curated scene presets and keyword router
│   └── config.py      # env-driven settings
├── static/
│   ├── index.html     # property page replica
│   ├── styles.css
│   └── app.js         # tabs + chat
├── workflows/         # drop flux_kontext.json here
├── requirements.txt
├── Dockerfile
└── README.md
```

## Endpoints

| Method | Path                | Purpose                                              |
|--------|---------------------|------------------------------------------------------|
| GET    | `/`                 | Property page (HTML)                                 |
| GET    | `/api/suggestions`  | The 4 cards rendered when the AI tab opens          |
| POST   | `/api/generate`     | `{prompt, guests}` → `{image_url, caption}`          |
| GET    | `/healthz`          | Liveness                                             |

## Notes for the vendor handoff

- The frontend is plain HTML/CSS/JS — no build step. Easy to splice into an
  existing site as a widget later.
- The AI panel is content-isolated to a single `<section data-panel="ai">`
  and can be lifted out wholesale.
- All prompts run through the curated `scenes.py` router today. When real
  ComfyUI is in place, keep the router as a safety layer (no nudity / no
  celebrity faces / generic fallback for unmatched prompts).
- Generated images are not persisted yet — add S3 / cache before going to
  production traffic.
