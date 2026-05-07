# Workflows

Drop your Flux Kontext workflow here as `flux_kontext.json`.

To export from ComfyUI:
1. Open the workflow in the ComfyUI canvas.
2. Settings → enable **Dev Mode**.
3. Click the **Save (API Format)** button (not the regular Save).
4. Save the file as `flux_kontext.json` in this directory.

After that, set `COMFYUI_URL=…` in `.env` and the backend will use it
automatically. Until either is missing, the mock generator in `app/comfy.py`
returns curated stock images.
