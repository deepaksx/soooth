# 4K Video Cache Setup

## Overview
This guide explains how to populate your S3 bucket with 100 high-quality 4K/HD videos for each theme (1,500 videos total).

## Prerequisites
- Pixabay API key configured in Render
- AWS S3 credentials configured
- S3 bucket: `soooth-media-library`

## Running on Render (Recommended)

### Option 1: SSH into Render Service

1. Go to https://dashboard.render.com
2. Click on `soooth-backend` service
3. Click the **Shell** tab (or use Render CLI)
4. Run the script:
   ```bash
   cd /opt/render/project/src/backend
   python bulk_download_videos.py
   ```

### Option 2: Temporary Job Service

1. In Render dashboard, create a new **Background Worker**
2. Use the same environment variables as your backend
3. Set start command to:
   ```bash
   cd backend && python bulk_download_videos.py
   ```
4. Deploy and monitor logs
5. Delete the worker once complete

## Running Locally

```bash
cd backend

# Make sure environment variables are set
export PIXABAY_API_KEY="your_key"
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="soooth-media-library"
export USE_S3_CACHE="true"
export DATABASE_URL="sqlite:///./soooth.db"

# Run the downloader
python bulk_download_videos.py
```

## What It Does

- Downloads **100 videos per theme** (15 themes total)
- Filters for **HD quality** (minimum 1920x1080)
- Searches with **"4k" keyword** for best quality
- Skips videos already in cache (safe to re-run)
- Uploads to S3 and cleans up local files immediately
- Tracks progress per theme

## Progress Tracking

The script will show:
```
================================================================================
Processing theme: FOREST
Search query: misty forest sunrise drone nature 4k
Target: 100 videos
================================================================================

[OK] Already cached: 4 videos
     Need to download: 96 more videos

  Fetching page 1...
  Found 200 videos on page 1
    Downloading 12345 (1920x1080)... [OK] (1/96)
    Downloading 67890 (3840x2160)... [OK] (2/96)
    ...
```

## Expected Duration

- **Per video**: ~5-10 seconds (download + upload to S3)
- **Per theme**: ~8-15 minutes (100 videos)
- **Total**: ~2-4 hours (1,500 videos)

Actual time depends on:
- Network speed
- Pixabay API rate limits
- S3 upload speed

## Monitoring

### Check cache size:
```bash
# From Render Shell or locally
cd backend
python -c "
from app.models import VideoCache, SessionLocal
db = SessionLocal()
for theme in ['forest', 'ocean', 'rain', 'mountain', 'meadow', 'starry_night', 'sunset', 'waterfall', 'lake', 'beach', 'clouds', 'snow', 'desert', 'aurora', 'flowers']:
    count = db.query(VideoCache).filter(VideoCache.theme == theme).count()
    print(f'{theme:15} {count:3} videos')
db.close()
"
```

### Check S3 storage:
- Go to AWS S3 Console
- Navigate to `soooth-media-library/videos/`
- View folder statistics

## Resume Interrupted Downloads

The script is **safe to re-run**. It will:
- Check existing cache before downloading
- Skip videos already in database
- Continue from where it left off

Just run the script again:
```bash
python bulk_download_videos.py
```

## Customization

Edit `bulk_download_videos.py` to customize:

```python
# Change target per theme (default: 100)
VIDEOS_PER_THEME = 150

# Add/remove themes
THEMES = {
    "forest": "misty forest sunrise drone nature 4k",
    "ocean": "ocean waves beach sunset aerial 4k",
    # ... add more themes
}

# Adjust quality filter (default: 1920x1080)
min_width=2560,  # For higher quality
min_height=1440,
```

## Troubleshooting

### ERROR: S3 cache is not enabled
- Check `USE_S3_CACHE=true` in environment
- Verify AWS credentials are set

### ERROR: Pixabay API key not configured
- Set `PIXABAY_API_KEY` environment variable

### Rate limit errors
- Pixabay limits: 5,000 requests/hour, 30,000 requests/day
- Script respects limits and will pause if needed
- Resume by running script again

### Low disk space
- Script cleans up files after S3 upload
- Only temporary storage needed (~100MB max)

## After Completion

Once complete, all video generation will:
- Use cached 4K/HD videos from S3
- Load much faster (no Pixabay API calls)
- Have consistent high quality
- Support offline generation

The cache is automatically used by the `pixabay.py` service.
