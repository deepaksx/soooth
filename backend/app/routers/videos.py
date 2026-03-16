from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models import Job, get_db
from app.schemas import JobResponse, JobListResponse
from app.config import settings

router = APIRouter(prefix="/api", tags=["videos"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of a generation job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(db: Session = Depends(get_db)):
    """List all generation jobs, newest first."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
    return JobListResponse(jobs=jobs)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running generation job."""
    from app.tasks.generate import cancel_pipeline

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("complete", "failed"):
        raise HTTPException(status_code=400, detail="Job already finished")
    job.status = "failed"
    job.error = "Cancelled by user"
    db.commit()

    # Actually kill the running task and FFmpeg
    cancel_pipeline(job_id)

    return {"status": "cancelled"}


@router.get("/videos/{job_id}")
def get_video(job_id: str, db: Session = Depends(get_db)):
    """Stream the generated video file by job ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "complete" or not job.output_path:
        raise HTTPException(status_code=404, detail="Video not ready yet")

    video_path = Path(job.output_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"soooth-{job.theme}-{job.id[:8]}.mp4",
    )


@router.get("/library/video/{filename}")
def get_library_video(filename: str):
    """Stream a video file from the output folder by filename."""
    # Sanitize filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files allowed")

    output_dir = settings.media_dir / "output"
    video_path = output_dir / filename

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename,
    )
