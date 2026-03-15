from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    fal_key: str = ""
    elevenlabs_api_key: str = ""
    pixabay_api_key: str = ""
    database_url: str = "sqlite:///./soooth.db"
    media_dir: Path = Path("C:/Dev/Soooth/media")

    # Video generation defaults
    video_model: str = "fal-ai/wan-t2v"
    video_duration: int = 5  # fal.ai generates short clips, we loop them

    # Music generation defaults
    music_duration: int = 60
    output_duration: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure media dirs exist
for subdir in ["videos", "audio", "output"]:
    (settings.media_dir / subdir).mkdir(parents=True, exist_ok=True)
