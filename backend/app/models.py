import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")  # pending | generating_video | generating_music | merging | complete | failed
    theme = Column(String, nullable=False)
    video_source = Column(String, default="ai")  # "ai" or "stock"
    no_audio = Column(String, default="false")  # "true" or "false"
    video_prompt = Column(Text, default="")
    music_prompt = Column(Text, default="")
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    custom_audio_path = Column(String, nullable=True)  # User-uploaded audio file
    output_path = Column(String, nullable=True)
    duration = Column(Integer, default=60)
    upload_youtube = Column(String, default="false")
    youtube_id = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class VideoCache(Base):
    """Cache for downloaded stock videos stored in S3."""
    __tablename__ = "video_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pixabay_id = Column(String, nullable=False, unique=True)  # Original Pixabay video ID
    theme = Column(String, nullable=False)  # Theme this video belongs to
    search_query = Column(String, nullable=False)  # Search term used
    s3_key = Column(String, nullable=False)  # S3 object key
    s3_url = Column(String, nullable=False)  # Full S3 URL
    duration = Column(Integer, nullable=False)  # Video duration in seconds
    width = Column(Integer, nullable=True)  # Video width
    height = Column(Integer, nullable=True)  # Video height
    file_size = Column(Integer, nullable=True)  # File size in bytes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used = Column(DateTime, nullable=True)  # Track when last used for LRU cleanup


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
