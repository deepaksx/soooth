from fastapi import APIRouter, HTTPException
from app.services.s3_cache import s3_cache
from app.services.youtube import upload_to_youtube
from app.config import settings
from pydantic import BaseModel
from pathlib import Path
import logging

logger = logging.getLogger("soooth.library")

router = APIRouter(prefix="/api/library", tags=["library"])


class LibraryFile(BaseModel):
    key: str
    url: str
    size: int
    last_modified: str


class LibraryResponse(BaseModel):
    files: list[LibraryFile]
    count: int
    folder: str


@router.get("/videos", response_model=LibraryResponse)
async def list_video_library():
    """List all cached stock video clips."""
    files = s3_cache.list_library("videos", limit=200)
    return LibraryResponse(
        files=files,
        count=len(files),
        folder="videos"
    )


@router.get("/audio", response_model=LibraryResponse)
async def list_audio_library():
    """List all generated audio files."""
    files = s3_cache.list_library("audio", limit=200)
    return LibraryResponse(
        files=files,
        count=len(files),
        folder="audio"
    )


@router.get("/output", response_model=LibraryResponse)
async def list_output_library():
    """List all final output videos."""
    files = s3_cache.list_library("output", limit=200)
    return LibraryResponse(
        files=files,
        count=len(files),
        folder="output"
    )


@router.get("/stats")
async def get_library_stats():
    """Get statistics about the media library."""
    videos = s3_cache.list_library("videos", limit=1000)
    audio = s3_cache.list_library("audio", limit=1000)
    output = s3_cache.list_library("output", limit=1000)

    return {
        "videos": {
            "count": len(videos),
            "total_size_mb": sum(f['size'] for f in videos) / (1024 * 1024)
        },
        "audio": {
            "count": len(audio),
            "total_size_mb": sum(f['size'] for f in audio) / (1024 * 1024)
        },
        "output": {
            "count": len(output),
            "total_size_mb": sum(f['size'] for f in output) / (1024 * 1024)
        }
    }


@router.get("/local-output")
async def list_local_output_videos():
    """List all videos in the local output folder."""
    output_dir = settings.media_dir / "output"

    if not output_dir.exists():
        return {"files": []}

    files = []
    for video_file in output_dir.glob("*.mp4"):
        stat = video_file.stat()
        files.append({
            "filename": video_file.name,
            "path": str(video_file),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime
        })

    # Sort by modified time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)

    return {"files": files, "count": len(files)}


class UploadVideoRequest(BaseModel):
    filename: str
    title: str = None
    description: str = None
    privacy: str = "public"  # public, unlisted, private


class DeleteFileRequest(BaseModel):
    key: str  # S3 key (e.g., "videos/forest/12345.mp4")


@router.post("/upload-to-youtube")
async def upload_video_to_youtube(request: UploadVideoRequest):
    """Upload an existing video from S3 or output folder to YouTube."""
    output_dir = settings.media_dir / "output"
    video_path = output_dir / request.filename

    # If file doesn't exist locally, try downloading from S3
    if not video_path.exists():
        if s3_cache.enabled:
            logger.info(f"Video not found locally, downloading from S3: {request.filename}")
            # Try to download from S3
            s3_key = f"output/{request.filename}"
            if not s3_cache.download_video(s3_key, video_path):
                raise HTTPException(status_code=404, detail=f"Video file not found in local storage or S3: {request.filename}")
        else:
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.filename}")

    try:
        logger.info(f"Uploading {request.filename} to YouTube with SEO optimization...")

        # Try to find the job by filename (filename format: job_id.mp4)
        job_id = request.filename.replace('.mp4', '')
        custom_audio_title = None

        from app.models import Job, SessionLocal
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job and job.custom_audio_filename:
                # Use original audio filename as YouTube title (without extension)
                custom_audio_title = job.custom_audio_filename.rsplit('.', 1)[0]
                logger.info(f"Found custom audio filename: {custom_audio_title}")
        finally:
            db.close()

        # Auto-detect theme from filename
        theme = "forest"  # Default theme
        filename_lower = request.filename.lower()

        # Try to detect theme from filename
        theme_keywords = {
            "forest": ["forest", "woodland", "trees"],
            "ocean": ["ocean", "beach", "waves", "sea"],
            "rain": ["rain", "rainfall"],
            "mountain": ["mountain", "alpine", "peak"],
            "meadow": ["meadow", "field", "grassland"],
            "starry_night": ["starry", "night", "stars"],
            "study_babe": ["study", "lofi"],
            "sunset": ["sunset", "golden"],
            "waterfall": ["waterfall", "cascade"],
        }

        for theme_name, keywords in theme_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                theme = theme_name
                break

        duration_minutes = 5  # Default duration

        # Try to extract duration from video file
        from app.services.media_merge import get_duration
        try:
            duration_seconds = int(get_duration(video_path))
            duration_minutes = max(1, duration_seconds // 60)
        except:
            pass

        # Use custom audio filename as title if available, otherwise use request title
        final_title = custom_audio_title or request.title

        # Log detected metadata
        logger.info(f"Detected theme: {theme}, duration: {duration_minutes} minutes")
        logger.info(f"Custom audio title: {custom_audio_title}")
        logger.info(f"Request title: {request.title}, description: {request.description}")
        logger.info(f"Final title: {final_title}")

        # Upload with full SEO optimization
        video_id = upload_to_youtube(
            video_path=str(video_path),
            title=final_title,  # Use custom audio filename or request title, or auto-SEO
            description=request.description,  # Will be None for auto-SEO
            theme=theme,
            duration_minutes=duration_minutes,
            privacy=request.privacy
        )

        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Successfully uploaded to YouTube: {youtube_url}")

        return {
            "success": True,
            "video_id": video_id,
            "url": youtube_url,
            "message": f"Video uploaded successfully!"
        }

    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/delete")
async def delete_file_from_s3(request: DeleteFileRequest):
    """Delete a file from S3 storage."""
    try:
        logger.info(f"Deleting file from S3: {request.key}")

        if not s3_cache.enabled:
            raise HTTPException(status_code=503, detail="S3 storage is not enabled")

        success = s3_cache.delete_file(request.key)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file from S3")

        return {
            "success": True,
            "message": f"File deleted successfully: {request.key}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
