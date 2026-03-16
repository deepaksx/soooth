import uuid
import random
import httpx
from pathlib import Path
from app.config import settings


async def search_and_download_videos(query: str, target_duration: int = 60) -> list[Path]:
    """Search Pixabay for stock videos and download enough to cover target duration.

    Downloads 6-10 clips, preferring longer videos. FFmpeg will loop if needed.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        # Search for videos — get more results to pick from
        resp = await client.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": settings.pixabay_api_key,
                "q": query,
                "video_type": "film",
                "per_page": 50,
                "safesearch": "true",
                "order": "popular",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            raise RuntimeError(f"No Pixabay videos found for: {query}")

        # Filter for landscape/horizontal videos only
        landscape_hits = [
            h for h in hits
            if h.get("videos", {}).get("large", {}).get("width", 0)
            >= h.get("videos", {}).get("large", {}).get("height", 999)
        ]
        if not landscape_hits:
            landscape_hits = hits

        # Sort by duration (longest first) to minimize number of clips needed
        landscape_hits.sort(key=lambda h: h.get("duration", 0), reverse=True)

        # Pick enough clips to cover target duration
        # Aim for ~8 unique clips max, FFmpeg will loop the concatenated result
        num_clips = min(8, len(landscape_hits))
        selected = random.sample(landscape_hits[:20], min(num_clips, len(landscape_hits[:20])))

        # Download each video
        clip_paths = []
        for hit in selected:
            videos = hit.get("videos", {})
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
