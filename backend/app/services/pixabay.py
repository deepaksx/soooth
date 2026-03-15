import uuid
import random
import httpx
from pathlib import Path
from app.config import settings


async def search_and_download_videos(query: str, num_clips: int = 6) -> list[Path]:
    """Search Pixabay for stock videos and download them."""
    async with httpx.AsyncClient(timeout=60) as client:
        # Search for videos
        resp = await client.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": settings.pixabay_api_key,
                "q": query,
                "video_type": "film",
                "per_page": 30,
                "safesearch": "true",
                "order": "popular",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            raise RuntimeError(f"No Pixabay videos found for: {query}")

        # Pick random selection from top results for variety
        selected = random.sample(hits, min(num_clips, len(hits)))

        # Download each video (prefer "medium" size for good quality + speed)
        clip_paths = []
        for hit in selected:
            videos = hit.get("videos", {})
            # Prefer large > medium > small
            video_info = videos.get("large") or videos.get("medium") or videos.get("small")
            if not video_info or not video_info.get("url"):
                continue

            output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"
            video_resp = await client.get(video_info["url"])
            video_resp.raise_for_status()
            output_path.write_bytes(video_resp.content)
            clip_paths.append(output_path)

        if len(clip_paths) < 2:
            raise RuntimeError(f"Only {len(clip_paths)} Pixabay clips downloaded — need at least 2")

        return clip_paths


# Search terms for each theme
PIXABAY_SEARCH_TERMS = {
    "forest": "misty forest sunrise drone nature",
    "ocean": "ocean waves beach sunset aerial",
    "rain": "rain drops leaves nature close up",
    "mountain": "mountain peaks clouds sunrise aerial",
    "meadow": "wildflower meadow breeze nature",
    "starry_night": "milky way stars night sky timelapse",
}
