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
    custom_audio_filename = Column(String, nullable=True)  # Original filename of uploaded audio
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


# Create engine with appropriate connect_args based on database type
if settings.database_url.startswith("sqlite"):
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

# Auto-migration: Add custom_audio_filename column if it doesn't exist
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check if column exists (PostgreSQL/SQLite compatible)
        if settings.database_url.startswith("sqlite"):
            result = conn.execute(text("PRAGMA table_info(jobs)"))
            columns = [row[1] for row in result]
        else:
            # PostgreSQL
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='jobs' AND column_name='custom_audio_filename'
            """))
            columns = [row[0] for row in result]

        if 'custom_audio_filename' not in columns:
            print("Running migration: Adding custom_audio_filename column...")
            conn.execute(text("ALTER TABLE jobs ADD COLUMN custom_audio_filename VARCHAR"))
            conn.commit()
            print("Migration complete: custom_audio_filename column added")
except Exception as e:
    print(f"Migration check failed (column may already exist): {e}")
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
