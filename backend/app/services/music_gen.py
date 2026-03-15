import os
import uuid
import httpx
from pathlib import Path
from app.config import settings

os.environ["FAL_KEY"] = settings.fal_key


async def generate_music(prompt: str, duration_seconds: int = 60) -> Path:
    """Generate instrumental music using fal.ai Stable Audio."""
    import fal_client

    output_path = settings.media_dir / "audio" / f"{uuid.uuid4()}.wav"

    # Stable Audio supports up to 47 seconds per generation
    # For 60s, we'll generate the max and FFmpeg will handle the rest
    gen_duration = min(duration_seconds, 47)

    result = await fal_client.subscribe_async(
        "fal-ai/stable-audio",
        arguments={
            "prompt": prompt,
            "seconds_total": gen_duration,
        },
    )

    # Download the audio file
    audio_url = result["audio_file"]["url"]
    async with httpx.AsyncClient(timeout=120) as client:
        audio_resp = await client.get(audio_url)
        audio_resp.raise_for_status()
        output_path.write_bytes(audio_resp.content)

    return output_path
