import asyncio
import subprocess
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Job
from app.services.video_gen import generate_video_clips
from app.services.music_gen import generate_music, generate_silent_audio
from app.services.pixabay import search_and_download_videos, PIXABAY_SEARCH_TERMS
from app.services.media_merge import concat_clips_with_crossfade, merge_audio_video
from app.services.youtube import upload_to_youtube
from app.services.s3_cache import s3_cache

# Track running tasks so they can be cancelled
_running_tasks: dict[str, asyncio.Task] = {}


def is_cancelled(job_id: str, db_session_factory) -> bool:
    """Check if a job has been cancelled by the user."""
    db = db_session_factory()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        return job is not None and job.status == "failed"
    finally:
        db.close()


async def run_generation_pipeline(job_id: str, db_session_factory):
    """Run the full video generation pipeline."""
    db: Session = db_session_factory()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "generating"
        db.commit()

        # Generate clips (AI or stock) and music simultaneously
        if job.video_source == "stock":
            # Handle multiple themes (comma-separated)
            themes = job.theme.split(",") if "," in job.theme else [job.theme]
            search_term = PIXABAY_SEARCH_TERMS.get(themes[0], themes[0])
            clips_task = search_and_download_videos(search_term, target_duration=job.duration, themes=themes)
        else:
            clips_task = generate_video_clips(job.video_prompt, num_clips=4)

        # Handle audio - use custom audio if provided, otherwise generate
        if job.custom_audio_path:
            # Use custom uploaded audio
            from pathlib import Path
            from app.services.media_merge import get_duration
            audio_path = Path(job.custom_audio_path)

            # Detect audio duration and update job
            audio_duration = int(get_duration(audio_path))
            job = db.query(Job).filter(Job.id == job_id).first()
            job.duration = audio_duration
            db.commit()

            clip_paths = await clips_task
        elif job.no_audio == "true":
            # Generate silent audio
            import logging
            logger = logging.getLogger("soooth.generate")
            logger.info(f"Starting silent audio generation for {job.duration}s")
            music_task = generate_silent_audio(job.duration)
            try:
                clip_paths, audio_path = await asyncio.gather(clips_task, music_task)
                logger.info(f"Silent audio generated: {audio_path}")
            except Exception as e:
                logger.error(f"Silent audio generation failed: {e}", exc_info=True)
                raise
        else:
            # Generate AI music
            music_task = generate_music(job.music_prompt, job.duration)
            clip_paths, audio_path = await asyncio.gather(clips_task, music_task)

        # Check if cancelled before merging
        if is_cancelled(job_id, db_session_factory):
            return

        job = db.query(Job).filter(Job.id == job_id).first()
        job.audio_path = str(audio_path)
        job.status = "merging"
        db.commit()

        # Upload audio to S3
        if s3_cache.enabled:
            s3_cache.upload_audio(audio_path, job_id)

        # Stock footage is already smooth — no slowdown needed
        slowdown = 1.0 if job.video_source == "stock" else 2.0
        concat_video = concat_clips_with_crossfade(clip_paths, job.duration, slowdown=slowdown)

        # Clean up individual clips to free memory (keep only concat video)
        import logging
        logger = logging.getLogger("soooth.generate")
        for clip in clip_paths:
            try:
                clip.unlink()
                logger.info(f"Cleaned up temp clip: {clip.name}")
            except Exception:
                pass

        # Check if cancelled before final merge
        if is_cancelled(job_id, db_session_factory):
            return

        output_path = merge_audio_video(concat_video, audio_path, job.duration)

        job = db.query(Job).filter(Job.id == job_id).first()
        job.video_path = str(concat_video)
        job.output_path = str(output_path)
        db.commit()

        # Upload output video to S3
        if s3_cache.enabled:
            s3_url = s3_cache.upload_output(output_path, job_id)
            if s3_url:
                job.output_path = s3_url
                db.commit()

                # Clean up local files after S3 upload to free memory
                try:
                    if concat_video.exists():
                        concat_video.unlink()
                        logger.info("Cleaned up concat video after S3 upload")
                except Exception:
                    pass

        # Upload to YouTube if requested
        if job.upload_youtube == "true":
            job.status = "uploading"
            db.commit()
            try:
                # Extract primary theme (first one if multiple)
                primary_theme = job.theme.split(",")[0] if "," in job.theme else job.theme
                duration_minutes = job.duration // 60 if job.duration >= 60 else 1

                # Upload with full SEO optimization
                video_id = upload_to_youtube(
                    str(output_path),
                    theme=primary_theme,
                    duration_minutes=duration_minutes,
                    privacy="public"
                )
                job.youtube_id = video_id
            except Exception as e:
                job.error = f"Video ready but YouTube upload failed: {e}"

        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except asyncio.CancelledError:
        # Task was cancelled — job status already set by cancel endpoint
        pass
    except Exception as e:
        db.rollback()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job and job.status != "failed":
                job.status = "failed"
                job.error = str(e)
                db.commit()
        except Exception:
            db2 = db_session_factory()
            try:
                job = db2.query(Job).filter(Job.id == job_id).first()
                if job and job.status != "failed":
                    job.status = "failed"
                    job.error = str(e)
                    db2.commit()
            finally:
                db2.close()
    finally:
        _running_tasks.pop(job_id, None)
        db.close()


def start_pipeline(job_id: str, db_session_factory):
    """Start the pipeline as a tracked asyncio task."""
    task = asyncio.create_task(run_generation_pipeline(job_id, db_session_factory))
    _running_tasks[job_id] = task
    return task


def cancel_pipeline(job_id: str):
    """Cancel a running pipeline task and kill any FFmpeg processes."""
    task = _running_tasks.get(job_id)
    if task and not task.done():
        task.cancel()

    # Kill any running FFmpeg processes to free files
    try:
        subprocess.run(
            ["pkill", "-f", "ffmpeg"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass
