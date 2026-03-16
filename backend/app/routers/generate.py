from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models import Job, get_db, SessionLocal
from app.schemas import GenerateRequest, JobResponse, BatchJobResponse, THEME_PROMPTS, get_random_study_babe_prompt
from app.tasks.generate import start_pipeline
from app.config import settings
from pathlib import Path
import uuid
from typing import Optional

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate", response_model=BatchJobResponse)
async def generate_video(
    theme: str = Form("forest"),
    video_source: str = Form("stock"),
    upload_youtube: bool = Form(False),
    no_audio: bool = Form(False),
    duration: int = Form(60),
    batch_count: int = Form(1),
    custom_video_prompt: Optional[str] = Form(None),
    custom_music_prompt: Optional[str] = Form(None),
    custom_audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Start new soothing video generation job(s). Supports batch generation and custom audio upload."""
    # Handle multi-theme (comma-separated string)
    themes_list = theme.split(",") if "," in theme else [theme]
    first_theme = themes_list[0]
    theme_data = THEME_PROMPTS.get(first_theme, THEME_PROMPTS["forest"])

    # Handle custom audio file upload
    custom_audio_path_str = None
    if custom_audio:
        audio_dir = settings.media_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded audio file
        file_ext = Path(custom_audio.filename).suffix or ".mp3"
        custom_audio_path = audio_dir / f"{uuid.uuid4()}_custom{file_ext}"

        content = await custom_audio.read()
        custom_audio_path.write_bytes(content)
        custom_audio_path_str = str(custom_audio_path)

    jobs = []
    batch_count_limit = max(1, min(batch_count, 20))  # Limit to 20 max

    for i in range(batch_count_limit):
        # For study_babe theme, generate random varied prompt if no custom prompt provided
        # Each iteration gets a DIFFERENT random prompt
        if theme == "study_babe" and not custom_video_prompt:
            video_prompt = get_random_study_babe_prompt()
        else:
            video_prompt = custom_video_prompt or theme_data["video"]

        music_prompt = custom_music_prompt or theme_data["music"]

        job = Job(
            theme=theme,
            video_source=video_source,
            upload_youtube="true" if upload_youtube else "false",
            no_audio="true" if no_audio else "false",
            video_prompt=video_prompt,
            music_prompt=music_prompt,
            duration=duration,
            custom_audio_path=custom_audio_path_str,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Start pipeline for this job
        start_pipeline(job.id, SessionLocal)

        jobs.append(job)

    return BatchJobResponse(jobs=jobs, batch_count=len(jobs))
