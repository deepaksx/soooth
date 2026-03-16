import boto3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from app.config import settings
from app.models import VideoCache, SessionLocal
from botocore.exceptions import ClientError

logger = logging.getLogger("soooth.s3")


class S3CacheService:
    """Service for caching videos in AWS S3."""

    def __init__(self):
        self.enabled = settings.use_s3_cache and settings.aws_access_key_id
        if self.enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket = settings.s3_bucket_name
            self._ensure_bucket_exists()
        else:
            logger.warning("S3 caching disabled - missing AWS credentials")

    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"S3 bucket {self.bucket} exists")
        except ClientError:
            try:
                if settings.aws_region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=self.bucket)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket,
                        CreateBucketConfiguration={'LocationConstraint': settings.aws_region}
                    )
                logger.info(f"Created S3 bucket {self.bucket}")
            except Exception as e:
                logger.error(f"Failed to create S3 bucket: {e}")

    def upload_video(self, local_path: Path, theme: str, pixabay_id: str, search_query: str,
                     duration: int, width: int = None, height: int = None) -> Optional[str]:
        """Upload stock video clip to S3 (videos/ folder) and store metadata in database."""
        if not self.enabled:
            return None

        try:
            # Generate S3 key: videos/{theme}/{pixabay_id}.mp4
            s3_key = f"videos/{theme}/{pixabay_id}.mp4"

            # Upload to S3
            self.s3_client.upload_file(
                str(local_path),
                self.bucket,
                s3_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )

            s3_url = f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded video to S3: {s3_url}")

            # Store metadata in database
            db = SessionLocal()
            try:
                cache_entry = VideoCache(
                    pixabay_id=pixabay_id,
                    theme=theme,
                    search_query=search_query,
                    s3_key=s3_key,
                    s3_url=s3_url,
                    duration=duration,
                    width=width,
                    height=height,
                    file_size=local_path.stat().st_size if local_path.exists() else None,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(cache_entry)
                db.commit()
                logger.info(f"Cached video metadata: {pixabay_id} for theme {theme}")
            finally:
                db.close()

            return s3_url

        except Exception as e:
            logger.error(f"Failed to upload video to S3: {e}")
            return None

    def upload_audio(self, local_path: Path, job_id: str) -> Optional[str]:
        """Upload generated audio to S3 (audio/ folder)."""
        if not self.enabled:
            return None

        try:
            file_ext = local_path.suffix
            s3_key = f"audio/{job_id}{file_ext}"

            self.s3_client.upload_file(
                str(local_path),
                self.bucket,
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )

            s3_url = f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded audio to S3: {s3_url}")
            return s3_url

        except Exception as e:
            logger.error(f"Failed to upload audio to S3: {e}")
            return None

    def upload_output(self, local_path: Path, job_id: str) -> Optional[str]:
        """Upload final output video to S3 (output/ folder)."""
        if not self.enabled:
            return None

        try:
            s3_key = f"output/{job_id}.mp4"

            self.s3_client.upload_file(
                str(local_path),
                self.bucket,
                s3_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )

            s3_url = f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded output video to S3: {s3_url}")
            return s3_url

        except Exception as e:
            logger.error(f"Failed to upload output to S3: {e}")
            return None

    def list_library(self, folder: str = "output", limit: int = 100) -> list[dict]:
        """List files in S3 library (audio, videos, or output)."""
        if not self.enabled:
            return []

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{folder}/",
                MaxKeys=limit
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'url': f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{obj['Key']}",
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })

            logger.info(f"Listed {len(files)} files from S3 {folder}/ folder")
            return files

        except Exception as e:
            logger.error(f"Failed to list S3 library: {e}")
            return []

    def download_video(self, s3_key: str, local_path: Path) -> bool:
        """Download video from S3 to local path."""
        if not self.enabled:
            return False

        try:
            self.s3_client.download_file(self.bucket, s3_key, str(local_path))
            logger.info(f"Downloaded video from S3: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to download video from S3: {e}")
            return False

    def get_cached_videos(self, themes: list[str], min_count: int = 8) -> list[VideoCache]:
        """Get cached videos for given themes from database."""
        if not self.enabled:
            return []

        db = SessionLocal()
        try:
            # Query videos matching any of the themes
            cached = db.query(VideoCache).filter(VideoCache.theme.in_(themes)).all()

            if len(cached) >= min_count:
                logger.info(f"Found {len(cached)} cached videos for themes: {themes}")

                # Update last_used timestamp
                for video in cached:
                    video.last_used = datetime.now(timezone.utc)
                db.commit()

                # Detach objects from session so they can be used after session closes
                db.expunge_all()
                return cached
            else:
                logger.info(f"Not enough cached videos ({len(cached)}/{min_count}) for themes: {themes}")
                return []
        finally:
            db.close()

    def is_video_cached(self, pixabay_id: str) -> Optional[VideoCache]:
        """Check if a video is already cached."""
        if not self.enabled:
            return None

        db = SessionLocal()
        try:
            cached = db.query(VideoCache).filter(VideoCache.pixabay_id == pixabay_id).first()
            if cached:
                # Detach object from session so it can be used after session closes
                db.expunge(cached)
            return cached
        finally:
            db.close()

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        if not self.enabled:
            logger.warning("S3 not enabled, cannot delete file")
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Deleted file from S3: {s3_key}")

            # If it's a video cache entry, also delete from database
            if s3_key.startswith("videos/"):
                db = SessionLocal()
                try:
                    # Extract filename from key to find the cache entry
                    filename = s3_key.split('/')[-1]
                    cache_entry = db.query(VideoCache).filter(VideoCache.s3_url.contains(filename)).first()
                    if cache_entry:
                        db.delete(cache_entry)
                        db.commit()
                        logger.info(f"Deleted cache entry for: {filename}")
                finally:
                    db.close()

            return True

        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False


# Global instance
s3_cache = S3CacheService()
