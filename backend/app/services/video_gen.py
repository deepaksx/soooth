import os
import uuid
import asyncio
import logging
import httpx
from pathlib import Path
from app.config import settings

logger = logging.getLogger("soooth.video")

os.environ["FAL_KEY"] = settings.fal_key

KLING_MODEL = "fal-ai/kling-video/v2.5-turbo/pro/text-to-video"
CLIP_TIMEOUT = 300  # 5 minutes max per clip


async def generate_single_clip(prompt: str, clip_index: int) -> Path:
    """Generate a single video clip using Kling via raw HTTP queue API."""
    output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"

    varied_prompt = f"{prompt}, variation {clip_index + 1}, unique angle and composition, ultra smooth fluid camera movement, no jitter, cinematic stabilized slow motion"
    logger.info(f"Clip {clip_index}: submitting to Kling...")

    async with httpx.AsyncClient(timeout=600) as client:
        submit_resp = await client.post(
            f"https://queue.fal.run/{KLING_MODEL}",
            headers={
                "Authorization": f"Key {settings.fal_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": varied_prompt,
                "duration": "5",
                "aspect_ratio": "16:9",
            },
        )
        submit_resp.raise_for_status()
        queue_data = submit_resp.json()

        status_url = queue_data["status_url"]
        response_url = queue_data["response_url"]

        # Poll with timeout
        elapsed = 0
        while elapsed < CLIP_TIMEOUT:
            await asyncio.sleep(5)
            elapsed += 5
            status_resp = await client.get(
                status_url,
                headers={"Authorization": f"Key {settings.fal_key}"},
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()
            status = status_data.get("status")

            if status == "COMPLETED":
                logger.info(f"Clip {clip_index}: completed in {elapsed}s")
                break
            elif status == "FAILED":
                logger.error(f"Clip {clip_index}: FAILED - {status_data}")
                raise RuntimeError(f"Video generation failed: {status_data}")
            elif elapsed % 30 == 0:
                logger.info(f"Clip {clip_index}: still {status} after {elapsed}s")
        else:
            logger.error(f"Clip {clip_index}: timed out after {CLIP_TIMEOUT}s")
            raise RuntimeError(f"Clip {clip_index} timed out after {CLIP_TIMEOUT}s")

        result_resp = await client.get(
            response_url,
            headers={"Authorization": f"Key {settings.fal_key}"},
        )
        result_resp.raise_for_status()
        result = result_resp.json()

        video_url = result["video"]["url"]
        video_resp = await client.get(video_url)
        video_resp.raise_for_status()
        output_path.write_bytes(video_resp.content)

    return output_path


async def generate_video_clips(prompt: str, num_clips: int = 4) -> list[Path]:
    """Generate multiple video clips in parallel. Tolerates individual failures."""
    tasks = [generate_single_clip(prompt, i) for i in range(num_clips)]

    # Run all clips concurrently with individual error handling
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failures — keep only successful clips
    clips = [r for r in results if isinstance(r, Path)]

    if len(clips) < 2:
        raise RuntimeError(f"Only {len(clips)} clips succeeded out of {num_clips} — need at least 2")

    return clips
