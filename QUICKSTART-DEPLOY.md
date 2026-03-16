# Quick Start: Deploy to Render in 15 Minutes

This is the fastest path to get Soooth running on Render with AWS S3.

## Step 1: AWS S3 (5 minutes)

```bash
# 1. Go to https://s3.console.aws.amazon.com/
# 2. Create bucket: "soooth-media-library" in us-east-1
# 3. Uncheck "Block all public access"
# 4. Add bucket policy (Permissions → Bucket Policy):
```

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::soooth-media-library/*"
  }]
}
```

```bash
# 5. Go to https://console.aws.amazon.com/iam/
# 6. Users → Create user → "soooth-render-user"
# 7. Attach policy: AmazonS3FullAccess
# 8. Create access key → Save the credentials!
```

## Step 2: Push to GitHub (2 minutes)

```bash
cd D:/Dev/Soooth/soooth
git add .
git commit -m "Deploy to Render with S3"
git push origin main
```

## Step 3: Deploy on Render (5 minutes)

1. Go to https://dashboard.render.com/
2. **New + → Blueprint**
3. **Connect** your GitHub repo
4. **Select** `soooth` repository
5. It will auto-detect `render.yaml`
6. **Add environment variables** (click each service):

### Backend Variables:
```
FAL_KEY = 2dc09451-1c3f-4973-bb64-e4f280b84829:66f7eb622a26bb16519b89a194875c1f
PIXABAY_API_KEY = 55036011-e6ae517c53bc01b73558e67ee
AWS_ACCESS_KEY_ID = AKIA...  (from AWS Step 1)
AWS_SECRET_ACCESS_KEY = wJalr...  (from AWS Step 1)
```

7. Click **"Apply"**
8. Wait ~8 minutes for build

## Step 4: Test (3 minutes)

1. Open: `https://soooth-frontend.onrender.com`
2. Select a theme (Forest)
3. Set duration: 1 min
4. Click Generate
5. Wait ~2 minutes
6. Video plays! ✅

## Verify S3 Working:

```bash
# Check your S3 bucket - you should see:
soooth-media-library/
├── videos/forest/12345.mp4
├── audio/job-id.mp3
└── output/job-id.mp4
```

## That's It! 🎉

Your app is live with:
- ✅ Frontend on Render
- ✅ Backend on Render
- ✅ Files stored in S3
- ✅ Video caching enabled

**URLs:**
- Frontend: `https://soooth-frontend.onrender.com`
- Backend: `https://soooth-backend.onrender.com`
- S3: `https://soooth-media-library.s3.amazonaws.com`

## Costs:
- Render: $14/month ($7/service × 2) or FREE tier
- AWS S3: ~$1/month for 100 videos
- **Total**: ~$15/month

## Troubleshooting:

**Backend fails to start?**
- Check environment variables are set
- Look at Render logs for errors

**Videos not saving to S3?**
- Verify AWS credentials are correct
- Check S3 bucket name matches `S3_BUCKET_NAME` variable

**CORS errors?**
- Frontend URL needs to be in backend CORS whitelist
- Already configured in `render.yaml`

For detailed guide, see: [DEPLOYMENT.md](./DEPLOYMENT.md)
