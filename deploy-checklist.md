# Soooth Deployment Checklist

Use this checklist when deploying to Render with AWS S3.

## Pre-Deployment

- [ ] Code pushed to GitHub repository
- [ ] All local changes committed
- [ ] Tested locally with all features working

## AWS S3 Setup

- [ ] Created S3 bucket: `soooth-media-library`
- [ ] Set bucket region: `us-east-1` (or your choice)
- [ ] Configured bucket policy for public read access
- [ ] Created IAM user: `soooth-render-user`
- [ ] Attached `AmazonS3FullAccess` policy
- [ ] Generated access keys (saved securely)
  - [ ] Access Key ID: `AKIA...`
  - [ ] Secret Access Key: `wJalr...`

## Render Setup

- [ ] Signed up/logged into Render.com
- [ ] Connected GitHub account to Render
- [ ] Selected repository: `soooth`

## Environment Variables (Backend)

Set these in Render Dashboard → soooth-backend → Environment:

- [ ] `FAL_KEY` = `2dc09451-1c3f-4973-bb64-e4f280b84829:66f7eb622a26bb16519b89a194875c1f`
- [ ] `PIXABAY_API_KEY` = `55036011-e6ae517c53bc01b73558e67ee`
- [ ] `AWS_ACCESS_KEY_ID` = Your AWS access key
- [ ] `AWS_SECRET_ACCESS_KEY` = Your AWS secret key
- [ ] `AWS_REGION` = `us-east-1`
- [ ] `S3_BUCKET_NAME` = `soooth-media-library`
- [ ] `USE_S3_CACHE` = `true`

## Environment Variables (Frontend)

- [ ] `VITE_API_URL` = `https://soooth-backend.onrender.com`
  - Update this to your actual backend URL if different

## Deployment

- [ ] Clicked "Apply" in Render Blueprint
- [ ] Waited for backend build to complete (~5 min)
- [ ] Waited for frontend build to complete (~3 min)
- [ ] Both services showing "Live" status
- [ ] No errors in deployment logs

## Post-Deployment Testing

- [ ] Visited frontend URL: `https://soooth-frontend.onrender.com`
- [ ] UI loads correctly
- [ ] Generated a test video (1 min, single theme)
- [ ] Video generation completed successfully
- [ ] Checked S3 bucket - files appeared in:
  - [ ] `videos/` folder
  - [ ] `audio/` folder
  - [ ] `output/` folder
- [ ] Library page shows generated video
- [ ] Video plays in library
- [ ] Second generation reuses cached videos (faster)

## Optional: YouTube Upload

- [ ] Decide if you want YouTube upload on production
- [ ] If yes: Configure OAuth credentials storage
- [ ] If no: Disable auto-upload feature in production

## Monitoring

- [ ] Bookmarked Render dashboard
- [ ] Bookmarked AWS S3 console
- [ ] Set up cost alerts in AWS
- [ ] Noted service URLs:
  - Frontend: `___________________________`
  - Backend: `___________________________`
  - S3 Bucket: `___________________________`

## Success Criteria

- [ ] Can generate videos from live site
- [ ] Videos are stored in S3
- [ ] Cached videos are reused (check logs)
- [ ] Library shows all generated videos
- [ ] No critical errors in logs
- [ ] S3 costs are reasonable

## Rollback Plan (If needed)

- [ ] Local version still works
- [ ] Can redeploy from previous commit
- [ ] AWS S3 bucket can be emptied/deleted
- [ ] Render services can be deleted

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Production URLs**:
- Frontend: _______________
- Backend: _______________

**Notes**:
_______________________________________
_______________________________________
_______________________________________
