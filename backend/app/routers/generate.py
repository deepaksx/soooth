from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import Job, get_db, SessionLocal
from app.schemas import GenerateRequest, JobResponse, THEME_PROMPTS
from app.tasks.generate import start_pipeline

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate", response_model=JobResponse)
async def generate_video(request: GenerateRequest, db: Session = Depends(get_db)):
    """Start a new soothing video generation job."""
    theme_data = THEME_PROMPTS.get(request.theme, THEME_PROMPTS["forest"])
    video_prompt = request.custom_video_prompt or theme_data["video"]
    music_prompt = request.custom_music_prompt or theme_data["music"]

    job = Job(
        theme=request.theme,
        video_source=request.video_source,
        upload_youtube="true" if request.upload_youtube else "false",
        video_prompt=video_prompt,
        music_prompt=music_prompt,
        duration=request.duration,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    start_pipeline(job.id, SessionLocal)

    return job
