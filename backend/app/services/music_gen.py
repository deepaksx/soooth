import uuid
import asyncio
import subprocess
import httpx
from pathlib import Path
from app.config import settings
from app.services.media_merge import FFMPEG


MAX_ELEVEN_DURATION = 300  # ElevenLabs max is 5 minutes per generation


async def _generate_single_track(client: httpx.AsyncClient, prompt: str, duration_ms: int) -> Path:
    """Generate a single music track from ElevenLabs."""
    output_path = settings.media_dir / "audio" / f"{uuid.uuid4()}.mp3"

    response = await client.post(
        "https://api.elevenlabs.io/v1/music",
        headers={
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "model_id": "music_v1",
            "music_length_ms": duration_ms,
        },
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


async def generate_music(prompt: str, duration_seconds: int = 60) -> Path:
    """Generate instrumental music. For durations > 5min, generates multiple tracks and joins."""

    if duration_seconds <= MAX_ELEVEN_DURATION:
        # Single generation
        async with httpx.AsyncClient(timeout=600) as client:
            return await _generate_single_track(client, prompt, duration_seconds * 1000)

    # For longer durations, generate multiple 5-min segments and concatenate
    segment_count = (duration_seconds + MAX_ELEVEN_DURATION - 1) // MAX_ELEVEN_DURATION
    segments = []

    async with httpx.AsyncClient(timeout=600) as client:
        remaining = duration_seconds
        for _ in range(segment_count):
            seg_dur = min(remaining, MAX_ELEVEN_DURATION)
            seg = await _generate_single_track(client, prompt, seg_dur * 1000)
            segments.append(seg)
            remaining -= seg_dur

    # Concatenate segments with FFmpeg crossfade
    if len(segments) == 1:
        return segments[0]

    output_path = settings.media_dir / "audio" / f"{uuid.uuid4()}.mp3"

    # Create concat file list
    list_path = settings.media_dir / "audio" / f"concat_{uuid.uuid4()}.txt"
    with open(list_path, "w") as f:
        for seg in segments:
            safe_path = str(seg).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    list_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(f"Audio concat failed: {proc.stderr[-500:]}")

    return output_path
