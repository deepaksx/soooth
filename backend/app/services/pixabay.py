import uuid
import random
import httpx
import logging
from pathlib import Path
from app.config import settings
from app.services.s3_cache import s3_cache

logger = logging.getLogger("soooth.pixabay")


async def search_and_download_videos(query: str, target_duration: int = 60, themes: list[str] = None) -> list[Path]:
    """Search Pixabay for stock videos and download enough to cover target duration.

    Downloads 6-10 clips, preferring longer videos. FFmpeg will loop if needed.
    If multiple themes provided, randomly mix videos from all themes.

    First checks S3 cache for existing videos before downloading from Pixabay.
    """
    # Try to use cached videos first
    if themes and s3_cache.enabled:
        cached_videos = s3_cache.get_cached_videos(themes, min_count=4)
        if cached_videos:
            logger.info(f"Using {len(cached_videos)} cached videos from S3")
            clip_paths = []

            # Download cached videos from S3 (limit to 4 for memory)
            for cached in random.sample(cached_videos, min(4, len(cached_videos))):
                output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"
                # cached is now a dict, not an object
                if s3_cache.download_video(cached['s3_key'], output_path):
                    clip_paths.append(output_path)

            if len(clip_paths) >= 2:
                logger.info(f"Successfully retrieved {len(clip_paths)} videos from cache")
                return clip_paths
            else:
                logger.warning("Failed to download enough cached videos, falling back to Pixabay")

    # Fall back to downloading from Pixabay
    async with httpx.AsyncClient(timeout=120) as client:
        all_hits = []

        # If multiple themes provided, search for each and combine results
        if themes and len(themes) > 1:
            for theme_id in themes:
                search_query = PIXABAY_SEARCH_TERMS.get(theme_id, theme_id)
                resp = await client.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": settings.pixabay_api_key,
                        "q": search_query,
                        "video_type": "film",
                        "per_page": 20,
                        "safesearch": "true",
                        "order": "popular",
                        "min_width": 1920,  # HD minimum for high quality
                        "min_height": 1080,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    all_hits.extend(data.get("hits", []))

            hits = all_hits
            if not hits:
                raise RuntimeError(f"No Pixabay videos found for selected themes")
        else:
            # Single theme search
            resp = await client.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": settings.pixabay_api_key,
                    "q": query,
                    "video_type": "film",
                    "per_page": 50,
                    "safesearch": "true",
                    "order": "popular",
                    "min_width": 1920,  # HD minimum for high quality
                    "min_height": 1080,
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
        # Limit to 4 clips to reduce memory usage (Render Standard has 2GB RAM)
        # FFmpeg will loop the concatenated result to reach target duration
        num_clips = min(4, len(landscape_hits))
        selected = random.sample(landscape_hits[:15], min(num_clips, len(landscape_hits[:15])))

        # Download each video
        clip_paths = []
        for hit in selected:
            videos = hit.get("videos", {})
            video_info = videos.get("large") or videos.get("medium") or videos.get("small")
            if not video_info or not video_info.get("url"):
                continue

            pixabay_id = str(hit.get("id", uuid.uuid4()))

            # Check if already cached in S3
            if s3_cache.enabled:
                cached = s3_cache.is_video_cached(pixabay_id)
                if cached:
                    logger.info(f"Video {pixabay_id} already cached, downloading from S3")
                    output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"
                    # cached is now a dict, not an object
                    if s3_cache.download_video(cached['s3_key'], output_path):
                        clip_paths.append(output_path)
                        continue

            # Download from Pixabay
            output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"
            video_resp = await client.get(video_info["url"])
            video_resp.raise_for_status()
            output_path.write_bytes(video_resp.content)
            clip_paths.append(output_path)

            # Upload to S3 cache
            if s3_cache.enabled and themes:
                theme_for_cache = themes[0] if len(themes) == 1 else "mixed"
                s3_cache.upload_video(
                    output_path,
                    theme=theme_for_cache,
                    pixabay_id=pixabay_id,
                    search_query=query,
                    duration=hit.get("duration", 10),
                    width=video_info.get("width"),
                    height=video_info.get("height")
                )
                logger.info(f"Uploaded video {pixabay_id} to S3 cache")

        if len(clip_paths) < 2:
            raise RuntimeError(f"Only {len(clip_paths)} Pixabay clips downloaded — need at least 2")

        return clip_paths


# Search terms for each theme (optimized for 4K/HD quality)
PIXABAY_SEARCH_TERMS = {
    "forest": "misty forest sunrise drone nature 4k",
    "ocean": "ocean waves beach sunset aerial 4k",
    "rain": "rain drops leaves nature close up 4k",
    "mountain": "mountain peaks clouds sunrise aerial 4k",
    "meadow": "wildflower meadow breeze nature 4k",
    "starry_night": "milky way stars night sky timelapse 4k",
    "sunset": "sunset golden hour horizon nature 4k",
    "waterfall": "waterfall cascade water nature 4k",
    "lake": "lake reflection calm water nature 4k",
    "beach": "beach sandy shore waves ocean 4k",
    "clouds": "clouds sky timelapse nature 4k",
    "snow": "snow winter snowfall nature 4k",
    "desert": "desert sand dunes sunset nature 4k",
    "aurora": "aurora northern lights night sky 4k",
    "flowers": "flowers blooming nature closeup 4k",
}
