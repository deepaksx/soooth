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
    video_prompt = Column(Text, default="")
    music_prompt = Column(Text, default="")
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    output_path = Column(String, nullable=True)
    duration = Column(Integer, default=60)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
