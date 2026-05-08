from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # The upstream wrapper endpoint that fronts ComfyUI. Accepts
    # multipart/form-data with `image` (file) + `prompt` (text), responds with
    # generated PNG bytes. Leave empty to use the mock generator.
    # Example: https://blush-fancy-science.ngrok-free.dev/run
    comfyui_endpoint: str = ""

    # Reference image used when the frontend doesn't pass one.
    default_reference_image: str = (
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b"
        "?auto=format&fit=crop&w=1200&q=70"
    )

    # Where generated PNGs are written. Lives under static/ so it's already
    # served at /static/generated/<file>.png by the StaticFiles mount.
    generated_dir: Path = _REPO_ROOT / "static" / "generated"

    # Cosmetic delay (seconds) on the mock generator so the chat shows a
    # "thinking" state — feels like the real flow even with no GPU.
    mock_delay_seconds: float = 1.4


settings = Settings()
