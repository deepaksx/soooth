# Soooth - Render Deployment Guide with AWS S3

This guide walks you through deploying Soooth on Render.com with AWS S3 for file storage and caching.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at https://render.com
3. **AWS Account** - For S3 bucket storage
4. **API Keys**:
   - fal.ai API key
   - Pixabay API key
   - (Optional) YouTube OAuth credentials

---

## Part 1: AWS S3 Setup

### Step 1: Create S3 Bucket

1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. Click **"Create bucket"**
3. Settings:
   - **Bucket name**: `soooth-media-library` (must be globally unique)
   - **Region**: `us-east-1` (or your preferred region)
   - **Block Public Access**: Uncheck (we need public read access for videos)
   - **Versioning**: Disabled
   - **Encryption**: Default (SSE-S3)
4. Click **"Create bucket"**

### Step 2: Configure Bucket Policy (Public Read Access)

1. Go to your bucket → **Permissions** → **Bucket Policy**
2. Add this policy (replace `soooth-media-library` with your bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::soooth-media-library/*"
    }
  ]
}
```

3. Click **"Save changes"**

### Step 3: Create IAM User for Programmatic Access

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click **"Users"** → **"Create user"**
3. Username: `soooth-render-user`
4. **Permissions**: Attach policies directly
   - Select **`AmazonS3FullAccess`**
5. Click **"Create user"**

### Step 4: Get Access Keys

1. Click on the user you just created
2. Go to **"Security credentials"** tab
3. Click **"Create access key"**
4. Use case: **"Application running outside AWS"**
5. **Save these credentials** (you'll need them for Render):
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalr...`

---

## Part 2: Render Deployment

### Step 1: Push Code to GitHub

```bash
cd D:/Dev/Soooth/soooth
git add .
git commit -m "Prepare for Render deployment with S3"
git push origin main
```

### Step 2: Connect Render to GitHub

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the `soooth` repository

### Step 3: Configure Environment Variables

Render will read from `render.yaml`, but you need to add secret values:

#### Backend Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `FAL_KEY` | `2dc09451-1c3f-4973-bb64-e4f280b84829:66f7eb622a26bb16519b89a194875c1f` | Your fal.ai API key |
| `PIXABAY_API_KEY` | `55036011-e6ae517c53bc01b73558e67ee` | Your Pixabay key |
| `AWS_ACCESS_KEY_ID` | `AKIA...` | From AWS IAM step |
| `AWS_SECRET_ACCESS_KEY` | `wJalr...` | From AWS IAM step |
| `AWS_REGION` | `us-east-1` | Match your S3 bucket region |
| `S3_BUCKET_NAME` | `soooth-media-library` | Your bucket name |
| `USE_S3_CACHE` | `true` | Enable S3 caching |

### Step 4: Deploy

1. Click **"Apply"** to deploy both services
2. Wait 5-10 minutes for initial build
3. Check deployment logs for any errors

---

## Part 3: Post-Deployment Configuration

### Update Frontend API URL

If your backend URL is different from `soooth-backend.onrender.com`:

1. Go to your frontend service in Render
2. **Environment** → **Add Environment Variable**:
   - Key: `VITE_API_URL`
   - Value: `https://your-actual-backend-url.onrender.com`
3. Click **"Save Changes"** → **"Manual Deploy"** → **"Deploy latest commit"**

### YouTube OAuth (Optional)

If you want YouTube upload functionality:

1. **Copy `youtube.json` to Render**:
   - You can't upload files directly to Render
   - Option A: Base64 encode the file and decode in app startup
   - Option B: Store credentials as environment variables
   - Option C: Use AWS Secrets Manager (recommended for production)

For now, you can skip YouTube upload on Render and only use it locally.

---

## Part 4: Verify Deployment

### Test the Application

1. **Visit your frontend**: `https://soooth-frontend.onrender.com`
2. **Test video generation**:
   - Select themes (Forest, Ocean, Rain)
   - Upload custom audio
   - Click Generate
3. **Check S3 bucket**:
   - Go to AWS S3 Console
   - Open `soooth-media-library`
   - You should see folders: `videos/`, `audio/`, `output/`

### Check Logs

1. Backend logs: Render Dashboard → soooth-backend → **Logs**
2. Look for:
   - ✅ `S3 bucket soooth-media-library exists`
   - ✅ `Uploaded video to S3: https://...`
   - ✅ `Successfully retrieved X videos from cache`

---

## Part 5: S3 Folder Structure

After running a few jobs, your S3 bucket will look like:

```
soooth-media-library/
├── videos/              # Cached Pixabay clips (reused across jobs)
│   ├── forest/
│   │   ├── 12345.mp4
│   │   └── 67890.mp4
│   ├── ocean/
│   └── mixed/
│
├── audio/               # Generated audio files
│   ├── job-id-1.mp3
│   └── job-id-2.mp3
│
└── output/              # Final rendered videos
    ├── job-id-1.mp4
    └── job-id-2.mp4
```

---

## Part 6: Cost Optimization

### S3 Costs (Estimated)

- **Storage**: ~$0.023/GB/month
- **Requests**: $0.0004 per 1,000 GET requests
- **Data Transfer**: First 100GB/month free

**Example**: 100 videos (~30GB) = $0.69/month

### Render Costs

- **Starter Plan**: $7/month per service
- **Total**: $14/month (backend + frontend)

### Free Tier Option

Use Render's **Free plan** for testing:
- Backend sleeps after 15 min inactivity
- 750 hours/month free

---

## Part 7: Monitoring & Maintenance

### Monitor S3 Usage

```bash
# Check bucket size
aws s3 ls s3://soooth-media-library --recursive --summarize
```

### Clear Old Videos (Cleanup)

Add a cleanup script to remove videos older than 30 days:

```python
# backend/scripts/cleanup_s3.py
from datetime import datetime, timedelta
import boto3

s3 = boto3.client('s3')
bucket = 'soooth-media-library'

# Delete videos older than 30 days
cutoff = datetime.now() - timedelta(days=30)
response = s3.list_objects_v2(Bucket=bucket, Prefix='videos/')

for obj in response.get('Contents', []):
    if obj['LastModified'].replace(tzinfo=None) < cutoff:
        s3.delete_object(Bucket=bucket, Key=obj['Key'])
        print(f"Deleted: {obj['Key']}")
```

---

## Troubleshooting

### Videos not caching?

Check backend logs for:
```
WARNING: S3 caching disabled - missing AWS credentials
```

**Fix**: Verify AWS environment variables are set in Render.

### CORS errors?

**Fix**: Update `backend/app/main.py` CORS settings:
```python
allow_origins=["https://your-frontend-url.onrender.com"]
```

### FFmpeg errors on Render?

Render includes FFmpeg by default. If issues occur:
```bash
# Add to buildCommand in render.yaml
apt-get update && apt-get install -y ffmpeg
```

---

## Success Checklist

- ✅ S3 bucket created and configured
- ✅ IAM user created with access keys
- ✅ Environment variables set in Render
- ✅ Both services deployed successfully
- ✅ Can generate videos from frontend
- ✅ Videos appear in S3 bucket
- ✅ Library page shows videos
- ✅ Second generation reuses cached videos (faster!)

---

## Next Steps

1. **Custom Domain**: Add your own domain in Render settings
2. **Analytics**: Add tracking with PostHog or Google Analytics
3. **Rate Limiting**: Add API rate limits for production
4. **CDN**: Use CloudFront for faster S3 downloads
5. **Database**: Upgrade to PostgreSQL for better persistence

---

## Support

- **Issues**: Create issue on GitHub
- **Render Docs**: https://render.com/docs
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/

Enjoy your production Soooth deployment! 🎉
