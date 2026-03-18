from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import httpx
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.services.s3_cache import s3_cache
from app.models import VideoCache, SessionLocal

logger = logging.getLogger("soooth.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Global state for bulk download
bulk_download_state = {
    "running": False,
    "started_at": None,
    "current_theme": None,
    "themes_completed": 0,
    "total_themes": 15,
    "videos_downloaded": 0,
    "current_theme_progress": {"downloaded": 0, "needed": 0},
    "error": None,
}


class BulkDownloadStatus(BaseModel):
    running: bool
    started_at: Optional[str]
    current_theme: Optional[str]
    themes_completed: int
    total_themes: int
    videos_downloaded: int
    current_theme_progress: dict
    error: Optional[str]
    s3_enabled: bool
    pixabay_configured: bool


THEMES = {
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

VIDEOS_PER_THEME = 100


def get_best_quality_url(videos_dict):
    """Get the highest quality video URL available."""
    for quality in ["large", "medium", "small"]:
        if quality in videos_dict and videos_dict[quality].get("url"):
            return videos_dict[quality]
    return None


async def download_videos_for_theme(theme: str, search_query: str, target_count: int = 100):
    """Download high-quality videos for a specific theme."""
    logger.info(f"Processing theme: {theme}")

    bulk_download_state["current_theme"] = theme
    bulk_download_state["current_theme_progress"] = {"downloaded": 0, "needed": 0}

    # Check existing cache
    db = SessionLocal()
    try:
        existing_count = db.query(VideoCache).filter(VideoCache.theme == theme).count()
        logger.info(f"Theme '{theme}' has {existing_count} cached videos")

        if existing_count >= target_count:
            logger.info(f"Theme '{theme}' already complete, skipping")
            return 0

        needed = target_count - existing_count
        bulk_download_state["current_theme_progress"]["needed"] = needed
        logger.info(f"Need to download {needed} more videos for '{theme}'")
    finally:
        db.close()

    downloaded = 0
    page = 1
    max_pages = 20

    async with httpx.AsyncClient(timeout=120) as client:
        while downloaded < needed and page <= max_pages:
            try:
                logger.info(f"Fetching page {page} for theme '{theme}'")
                resp = await client.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": settings.pixabay_api_key,
                        "q": search_query,
                        "video_type": "film",
                        "per_page": 200,
                        "page": page,
                        "safesearch": "true",
                        "order": "popular",
                        "min_width": 1920,
                        "min_height": 1080,
                    },
                )

                if resp.status_code != 200:
                    logger.error(f"API request failed: {resp.status_code}")
                    break

                data = resp.json()
                hits = data.get("hits", [])

                if not hits:
                    logger.info(f"No more videos found on page {page}")
                    break

                logger.info(f"Found {len(hits)} videos on page {page}")

                for hit in hits:
                    if downloaded >= needed:
                        break

                    pixabay_id = str(hit.get("id"))

                    # Skip if already in cache
                    db = SessionLocal()
                    try:
                        exists = db.query(VideoCache).filter(
                            VideoCache.pixabay_id == pixabay_id
                        ).first()
                        if exists:
                            continue
                    finally:
                        db.close()

                    videos = hit.get("videos", {})
                    video_info = get_best_quality_url(videos)

                    if not video_info or not video_info.get("url"):
                        continue

                    width = video_info.get("width", 0)
                    height = video_info.get("height", 0)

                    # Filter for landscape and HD quality
                    if width < height or width < 1920 or height < 1080:
                        continue

                    try:
                        logger.info(f"Downloading {pixabay_id} ({width}x{height})")

                        output_path = settings.media_dir / "videos" / f"{uuid.uuid4()}.mp4"
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        video_resp = await client.get(video_info["url"])
                        video_resp.raise_for_status()
                        output_path.write_bytes(video_resp.content)

                        # Upload to S3
                        if s3_cache.enabled:
                            s3_cache.upload_video(
                                output_path,
                                theme=theme,
                                pixabay_id=pixabay_id,
                                search_query=search_query,
                                duration=hit.get("duration", 10),
                                width=width,
                                height=height
                            )

                            output_path.unlink()
                            downloaded += 1

                            # Update state
                            bulk_download_state["videos_downloaded"] += 1
                            bulk_download_state["current_theme_progress"]["downloaded"] = downloaded

                            logger.info(f"Successfully uploaded {pixabay_id} ({downloaded}/{needed})")

                    except Exception as e:
                        logger.error(f"Failed to download {pixabay_id}: {e}")
                        continue

                page += 1

            except Exception as e:
                logger.error(f"Page {page} failed: {e}")
                break

    logger.info(f"Downloaded {downloaded} new videos for theme '{theme}'")
    return downloaded


async def run_bulk_download():
    """Run the bulk download process."""
    if bulk_download_state["running"]:
        logger.warning("Bulk download already running")
        return

    try:
        bulk_download_state["running"] = True
        bulk_download_state["started_at"] = datetime.now(timezone.utc).isoformat()
        bulk_download_state["themes_completed"] = 0
        bulk_download_state["videos_downloaded"] = 0
        bulk_download_state["error"] = None

        logger.info("Starting bulk video download")

        for theme, search_query in THEMES.items():
            try:
                await download_videos_for_theme(theme, search_query, VIDEOS_PER_THEME)
                bulk_download_state["themes_completed"] += 1
            except Exception as e:
                logger.error(f"Theme '{theme}' failed: {e}")
                bulk_download_state["error"] = f"Theme '{theme}' failed: {str(e)}"
                continue

        logger.info("Bulk download complete")

    except Exception as e:
        logger.error(f"Bulk download failed: {e}")
        bulk_download_state["error"] = str(e)
    finally:
        bulk_download_state["running"] = False
        bulk_download_state["current_theme"] = None


@router.get("/bulk-download/status", response_model=BulkDownloadStatus)
async def get_bulk_download_status():
    """Get the current status of the bulk download process."""
    return BulkDownloadStatus(
        running=bulk_download_state["running"],
        started_at=bulk_download_state["started_at"],
        current_theme=bulk_download_state["current_theme"],
        themes_completed=bulk_download_state["themes_completed"],
        total_themes=bulk_download_state["total_themes"],
        videos_downloaded=bulk_download_state["videos_downloaded"],
        current_theme_progress=bulk_download_state["current_theme_progress"],
        error=bulk_download_state["error"],
        s3_enabled=bool(s3_cache.enabled),
        pixabay_configured=bool(settings.pixabay_api_key),
    )


@router.post("/bulk-download/start")
async def start_bulk_download(background_tasks: BackgroundTasks):
    """Start the bulk video download process."""
    if bulk_download_state["running"]:
        raise HTTPException(status_code=400, detail="Bulk download already running")

    if not s3_cache.enabled:
        raise HTTPException(status_code=400, detail="S3 cache is not enabled")

    if not settings.pixabay_api_key:
        raise HTTPException(status_code=400, detail="Pixabay API key not configured")

    # Start the download in the background
    background_tasks.add_task(run_bulk_download)

    return {
        "success": True,
        "message": "Bulk download started",
        "target": f"{VIDEOS_PER_THEME} videos per theme",
        "total_themes": len(THEMES),
        "total_target": VIDEOS_PER_THEME * len(THEMES),
    }


@router.post("/bulk-download/stop")
async def stop_bulk_download():
    """Stop the bulk download process (if running)."""
    if not bulk_download_state["running"]:
        raise HTTPException(status_code=400, detail="No bulk download is running")

    # Note: This just sets the flag, the actual task will complete its current theme
    bulk_download_state["running"] = False
    bulk_download_state["error"] = "Stopped by user"

    return {
        "success": True,
        "message": "Bulk download stop requested (will finish current theme)",
    }


@router.get("/cache-stats")
async def get_cache_stats():
    """Get statistics about the video cache."""
    db = SessionLocal()
    try:
        stats = {}
        for theme in THEMES.keys():
            count = db.query(VideoCache).filter(VideoCache.theme == theme).count()
            stats[theme] = {
                "count": count,
                "target": VIDEOS_PER_THEME,
                "percentage": int((count / VIDEOS_PER_THEME) * 100) if VIDEOS_PER_THEME > 0 else 0,
            }

        total_count = db.query(VideoCache).count()
        total_target = VIDEOS_PER_THEME * len(THEMES)

        return {
            "themes": stats,
            "total": {
                "count": total_count,
                "target": total_target,
                "percentage": int((total_count / total_target) * 100) if total_target > 0 else 0,
            },
        }
    finally:
        db.close()
