import asyncio
import subprocess
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Job
from app.services.video_gen import generate_video_clips
from app.services.music_gen import generate_music
from app.services.pixabay import search_and_download_videos, PIXABAY_SEARCH_TERMS
from app.services.media_merge import concat_clips_with_crossfade, merge_audio_video

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
            search_term = PIXABAY_SEARCH_TERMS.get(job.theme, job.theme)
            clips_task = search_and_download_videos(search_term, num_clips=6)
        else:
            clips_task = generate_video_clips(job.video_prompt, num_clips=4)

        music_task = generate_music(job.music_prompt, job.duration)

        clip_paths, audio_path = await asyncio.gather(clips_task, music_task)

        # Check if cancelled before merging
        if is_cancelled(job_id, db_session_factory):
            return

        job = db.query(Job).filter(Job.id == job_id).first()
        job.audio_path = str(audio_path)
        job.status = "merging"
        db.commit()

        # Stock footage is already smooth — no slowdown needed
        slowdown = 1.0 if job.video_source == "stock" else 2.0
        concat_video = concat_clips_with_crossfade(clip_paths, job.duration, slowdown=slowdown)

        # Check if cancelled before final merge
        if is_cancelled(job_id, db_session_factory):
            return

        output_path = merge_audio_video(concat_video, audio_path, job.duration)

        job = db.query(Job).filter(Job.id == job_id).first()
        job.video_path = str(concat_video)
        job.output_path = str(output_path)
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
