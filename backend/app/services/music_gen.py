import uuid
import asyncio
import subprocess
import httpx
from pathlib import Path
from app.config import settings
from app.services.media_merge import FFMPEG
import fal_client


async def generate_silent_audio(duration_seconds: int = 60) -> Path:
    """Generate silent audio track."""
    output_path = settings.media_dir / "audio" / f"{uuid.uuid4()}_silent.mp3"

    # Generate silent audio using ffmpeg (synchronous to avoid Windows asyncio issues)
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration_seconds),
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(output_path),
    ]

    def run_ffmpeg():
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Silent audio generation failed: {proc.stderr.decode()[-500:]}")
        return output_path

    return await asyncio.to_thread(run_ffmpeg)


async def generate_music(prompt: str, duration_seconds: int = 60) -> Path:
    """Generate music using fal.ai's audio generation models."""
    output_path = settings.media_dir / "audio" / f"{uuid.uuid4()}.mp3"

    # Configure fal client
    fal_client.api_key = settings.fal_key

    try:
        # Use fal.ai's music generation model
        # Available models: stable-audio, musicgen, etc.
        result = await asyncio.to_thread(
            fal_client.subscribe,
            "fal-ai/stable-audio",
            arguments={
                "prompt": prompt,
                "seconds_total": min(duration_seconds, 47),  # stable-audio max is 47s
                "cfg_scale": 7.0,
            }
        )

        # Download the generated audio
        audio_url = result.get("audio_file", {}).get("url")
        if not audio_url:
            raise RuntimeError("No audio URL in fal.ai response")

        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)

        # If duration > 47s, loop the audio to match the requested duration
        if duration_seconds > 47:
            looped_path = settings.media_dir / "audio" / f"{uuid.uuid4()}_looped.mp3"
            loop_count = (duration_seconds + 46) // 47  # Round up

            cmd = [
                FFMPEG, "-y",
                "-stream_loop", str(loop_count - 1),
                "-i", str(output_path),
                "-t", str(duration_seconds),
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                str(looped_path),
            ]

            def loop_audio():
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"Audio looping failed: {proc.stderr.decode()[-500:]}")

            await asyncio.to_thread(loop_audio)

            # Replace original with looped version
            output_path.unlink()
            output_path = looped_path

        return output_path

    except Exception as e:
        raise RuntimeError(f"fal.ai music generation failed: {str(e)}")
