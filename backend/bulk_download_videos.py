#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk download high-quality 4K videos from Pixabay for all themes.
Downloads 100 videos per theme and uploads to S3 cache.

Usage:
    python bulk_download_videos.py

Requirements:
    - PIXABAY_API_KEY environment variable
    - AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - USE_S3_CACHE=true
"""
import asyncio
import httpx
import uuid
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.s3_cache import s3_cache
from app.models import VideoCache, SessionLocal

# All themes to populate
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
    """Get the highest quality video URL available (4K > HD > large > medium > small)."""
    # Pixabay quality hierarchy
    for quality in ["large", "medium", "small"]:
        if quality in videos_dict and videos_dict[quality].get("url"):
            return videos_dict[quality]
    return None


async def download_videos_for_theme(theme: str, search_query: str, target_count: int = 100):
    """Download high-quality videos for a specific theme."""
    print(f"\n{'='*80}")
    print(f"Processing theme: {theme.upper()}")
    print(f"Search query: {search_query}")
    print(f"Target: {target_count} videos")
    print(f"{'='*80}\n")

    # Check existing cache
    db = SessionLocal()
    try:
        existing_count = db.query(VideoCache).filter(VideoCache.theme == theme).count()
        print(f"[OK] Already cached: {existing_count} videos")

        if existing_count >= target_count:
            print(f"[OK] Theme '{theme}' already has {existing_count} videos (target: {target_count})")
            print(f"     Skipping download for this theme.\n")
            return existing_count

        needed = target_count - existing_count
        print(f"     Need to download: {needed} more videos\n")
    finally:
        db.close()

    downloaded = 0
    page = 1
    max_pages = 20  # Pixabay limit

    async with httpx.AsyncClient(timeout=120) as client:
        while downloaded < needed and page <= max_pages:
            try:
                print(f"  Fetching page {page}...")
                resp = await client.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": settings.pixabay_api_key,
                        "q": search_query,
                        "video_type": "film",
                        "per_page": 200,  # Max allowed
                        "page": page,
                        "safesearch": "true",
                        "order": "popular",
                        "min_width": 1920,  # HD minimum
                        "min_height": 1080,
                    },
                )

                if resp.status_code != 200:
                    print(f"  [ERROR] API request failed: {resp.status_code}")
                    break

                data = resp.json()
                hits = data.get("hits", [])

                if not hits:
                    print(f"  [INFO] No more videos found on page {page}")
                    break

                print(f"  Found {len(hits)} videos on page {page}")

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

                    # Get best quality video
                    videos = hit.get("videos", {})
                    video_info = get_best_quality_url(videos)

                    if not video_info or not video_info.get("url"):
                        continue

                    # Filter for landscape orientation
                    width = video_info.get("width", 0)
                    height = video_info.get("height", 0)
                    if width < height:
                        continue  # Skip portrait videos

                    # Filter for high quality (at least 1920x1080)
                    if width < 1920 or height < 1080:
                        continue

                    try:
                        # Download video
                        print(f"    Downloading {pixabay_id} ({width}x{height})...", end=" ")

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

                            # Clean up local file to save disk space
                            output_path.unlink()

                            downloaded += 1
                            print(f"[OK] ({downloaded}/{needed})")
                        else:
                            print("[ERROR] S3 not enabled")
                            output_path.unlink()

                    except Exception as e:
                        print(f"[ERROR] {e}")
                        continue

                page += 1

            except Exception as e:
                print(f"  [ERROR] Page {page} failed: {e}")
                break

    print(f"\n[OK] Downloaded {downloaded} new videos for theme '{theme}'")
    return downloaded


async def main():
    """Download videos for all themes."""
    print("="*80)
    print("BULK VIDEO DOWNLOAD - 4K/HD Quality")
    print("="*80)
    print(f"Target: {VIDEOS_PER_THEME} videos per theme")
    print(f"Themes: {len(THEMES)}")
    print(f"Total target: {VIDEOS_PER_THEME * len(THEMES)} videos")
    print(f"S3 Bucket: {settings.s3_bucket_name}")
    print("="*80)

    if not s3_cache.enabled:
        print("\n[ERROR] S3 cache is not enabled!")
        print("        Set USE_S3_CACHE=true and configure AWS credentials.")
        return

    if not settings.pixabay_api_key:
        print("\n[ERROR] Pixabay API key not configured!")
        return

    start_time = datetime.now()
    total_downloaded = 0

    for theme, search_query in THEMES.items():
        try:
            count = await download_videos_for_theme(theme, search_query, VIDEOS_PER_THEME)
            total_downloaded += count
        except Exception as e:
            print(f"\n[ERROR] Theme '{theme}' failed: {e}\n")
            continue

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("BULK DOWNLOAD COMPLETE")
    print("="*80)
    print(f"Total videos downloaded: {total_downloaded}")
    print(f"Time taken: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    if total_downloaded > 0:
        print(f"Average: {duration/total_downloaded:.1f} seconds per video")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
