from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Set this once the ComfyUI server is reachable. While empty, the backend
    # serves stubbed/mock images so the demo is usable end-to-end.
    comfyui_url: str = ""
    comfyui_workflow_path: str = "workflows/flux_kontext.json"

    # Default reference image fed into Flux Kontext for this MVP.
    # Replace per-property when wired up to a real catalogue.
    default_reference_image: str = (
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b"
        "?auto=format&fit=crop&w=1200&q=70"
    )

    # Cosmetic delay (seconds) on the mock generator so the UI shows a
    # "thinking" state — feels more like the real flow.
    mock_delay_seconds: float = 1.4


settings = Settings()
