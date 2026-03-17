import os
import json
import logging
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("soooth.youtube")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# Path from: backend/app/services/youtube.py -> up 4 levels to soooth/
CLIENT_SECRET_FILE = Path(__file__).parent.parent.parent.parent / "youtube.json"
TOKEN_FILE = Path(__file__).parent.parent.parent.parent / "youtube_token.json"


def get_youtube_service():
    """Get authenticated YouTube API service.

    Supports both file-based (local dev) and env-based (production) credentials.
    """
    creds = None

    # Try environment variables first (for Render deployment)
    youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON")
    youtube_client_json = os.getenv("YOUTUBE_CLIENT_JSON")

    if youtube_token_json:
        # Load credentials from environment variable
        logger.info("Using YouTube credentials from environment variables")
        try:
            # Clean the JSON string by removing control characters
            import re
            cleaned_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', youtube_token_json)

            # Log for debugging (first 50 chars only to avoid exposing full tokens)
            logger.info(f"Raw JSON length: {len(youtube_token_json)}, Cleaned length: {len(cleaned_json)}")
            if len(youtube_token_json) != len(cleaned_json):
                logger.warning(f"Removed {len(youtube_token_json) - len(cleaned_json)} control characters from JSON")

            token_data = json.loads(cleaned_json)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)

            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired YouTube token")
                creds.refresh(Request())
                # Note: Updated token is not saved back to env var (manual update needed)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse YouTube credentials JSON: {e}")
            logger.error(f"Character at error position: {repr(youtube_token_json[max(0, e.pos-10):e.pos+10])}")
            raise RuntimeError("YouTube upload not configured. Invalid JSON format in YOUTUBE_TOKEN_JSON environment variable.")
        except Exception as e:
            logger.error(f"Failed to load YouTube credentials from env: {e}")
            raise RuntimeError("YouTube upload not configured. Missing or invalid YOUTUBE_TOKEN_JSON environment variable.")

    elif TOKEN_FILE.exists():
        # Fall back to file-based credentials (local development)
        logger.info("Using YouTube credentials from local files")
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CLIENT_SECRET_FILE.exists():
                    raise RuntimeError("YouTube client secrets file not found. Please add youtube.json or set YOUTUBE_CLIENT_JSON environment variable.")
                flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
                creds = flow.run_local_server(port=8090, open_browser=True)

            # Save token for future use
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
    else:
        # No credentials available
        raise RuntimeError(
            "YouTube upload not configured. Please either:\n"
            "1. Run authentication locally first to generate youtube_token.json, OR\n"
            "2. Set YOUTUBE_TOKEN_JSON environment variable in Render"
        )

    return build("youtube", "v3", credentials=creds)


def generate_seo_optimized_metadata(theme: str, duration_minutes: int) -> dict:
    """Generate SEO-optimized title, description, and tags for YouTube."""

    # Theme-specific keywords and descriptions
    theme_data = {
        "forest": {
            "keywords": ["forest sounds", "nature sounds", "woodland", "trees", "birdsong", "forest ambience"],
            "scenery": "misty forest at sunrise with gentle light rays",
            "mood": "peaceful woodland atmosphere",
            "benefits": "stress relief, deep sleep, meditation, focus",
        },
        "ocean": {
            "keywords": ["ocean waves", "beach sounds", "sea sounds", "coastal", "water sounds", "ocean ambience"],
            "scenery": "calm ocean waves on pristine white sand beach",
            "mood": "tranquil seaside atmosphere",
            "benefits": "relaxation, sleep aid, anxiety relief, meditation",
        },
        "rain": {
            "keywords": ["rain sounds", "rainfall", "rain on leaves", "gentle rain", "rain ambience", "rainstorm"],
            "scenery": "gentle rain falling on lush green leaves",
            "mood": "cozy and calming rainy day",
            "benefits": "deep sleep, study focus, stress relief, insomnia relief",
        },
        "mountain": {
            "keywords": ["mountain sounds", "nature ambience", "alpine", "peak views", "mountain wind"],
            "scenery": "majestic snow-capped mountain peaks above clouds",
            "mood": "serene mountain atmosphere",
            "benefits": "meditation, focus, relaxation, mental clarity",
        },
        "meadow": {
            "keywords": ["meadow sounds", "field sounds", "nature sounds", "grassland", "summer breeze"],
            "scenery": "wildflowers swaying in gentle breeze",
            "mood": "peaceful countryside atmosphere",
            "benefits": "stress relief, relaxation, peaceful sleep, meditation",
        },
        "starry_night": {
            "keywords": ["night sounds", "starry sky", "milky way", "night ambience", "astronomy"],
            "scenery": "crystal clear starry night sky with Milky Way",
            "mood": "peaceful nocturnal atmosphere",
            "benefits": "deep sleep, insomnia relief, meditation, stargazing",
        },
        "study_babe": {
            "keywords": ["study music", "lofi", "study ambience", "work music", "focus music", "study with me"],
            "scenery": "elegant study setting with glamorous atmosphere",
            "mood": "sophisticated and focused study environment",
            "benefits": "concentration, productivity, study focus, work motivation",
        },
        "sunset": {
            "keywords": ["sunset sounds", "golden hour", "evening ambience", "sunset views", "peaceful evening"],
            "scenery": "breathtaking golden sunset over horizon",
            "mood": "warm and peaceful evening atmosphere",
            "benefits": "relaxation, meditation, evening wind-down, stress relief",
        },
        "waterfall": {
            "keywords": ["waterfall sounds", "cascading water", "nature sounds", "flowing water", "water ambience"],
            "scenery": "majestic waterfall cascading through lush nature",
            "mood": "powerful yet soothing water atmosphere",
            "benefits": "stress relief, sleep aid, meditation, tinnitus relief",
        },
    }

    # Get theme data or use default
    theme_info = theme_data.get(theme, theme_data["forest"])
    theme_label = theme.replace("_", " ").title()

    # SEO-optimized title (under 60 characters for best display)
    if duration_minutes >= 60:
        hours = duration_minutes // 60
        duration_str = f"{hours} HOUR" if hours == 1 else f"{hours} HOURS"
    else:
        duration_str = f"{duration_minutes} MIN"

    title = f"{theme_label} Sounds {duration_str} 🌿 {theme_info['benefits'].split(',')[0].strip().title()}"
    title = title[:100]  # YouTube max is 100 chars

    # SEO-optimized description with keywords, timestamps, and structure
    description = f"""🎧 {duration_str} of Soothing {theme_label} Sounds | Perfect for Sleep, Study, Relaxation & Meditation

✨ WHAT YOU'LL EXPERIENCE:
Immerse yourself in {theme_info['scenery']} with calming ambient music. This {duration_minutes}-minute video creates the perfect {theme_info['mood']} for your relaxation needs.

🌟 BENEFITS:
✓ {theme_info['benefits'].replace(',', '\n✓ ').strip()}
✓ Background ambience for work or study
✓ Natural sound therapy
✓ Stress and anxiety reduction

⏰ TIMESTAMPS:
00:00 - Introduction
00:30 - Begin Relaxation Journey
{duration_minutes - 5}:00 - Final Minutes
{duration_minutes}:00 - End

🎵 PERFECT FOR:
• Sleep and Deep Rest (insomnia relief)
• Study & Focus (concentration booster)
• Meditation & Yoga (mindfulness practice)
• Work & Productivity (ambient background)
• Stress Relief & Anxiety Management
• ASMR Relaxation
• White Noise Alternative
• Tinnitus Relief
• Baby Sleep Aid
• Spa & Massage Ambience

🌍 WHY {theme_label.upper()} SOUNDS?
Nature sounds and ambient music have been scientifically proven to reduce stress, improve sleep quality, enhance focus, and promote overall well-being. This video combines beautiful {theme_label.lower()} imagery with carefully crafted soundscapes to create the ultimate relaxation experience.

💤 SLEEP BETTER:
Use this as your bedtime routine. The gentle sounds will help you fall asleep faster and stay asleep longer. Perfect for those struggling with insomnia or restless nights.

📚 STUDY SMARTER:
Create the perfect study environment. The ambient background helps maintain focus without being distracting. Ideal for students, remote workers, and anyone needing concentration.

🧘 MEDITATE DEEPER:
Enhance your meditation practice with natural soundscapes. Perfect for guided meditation, mindfulness exercises, or simply finding your inner peace.

🎯 RECOMMENDED USAGE:
• Turn off autoplay for continuous relaxation
• Use headphones for the best experience
• Adjust volume to comfortable level
• Loop for extended sessions
• Combine with aromatherapy for enhanced relaxation

🔔 SUBSCRIBE FOR MORE:
Get weekly uploads of premium nature sounds, ambient music, and relaxation videos. Build your personal library of peace and tranquility.

📱 SHARE THE CALM:
Know someone who needs to relax? Share this video with friends and family who could benefit from natural stress relief.

---

🏷️ KEYWORDS:
{', '.join(theme_info['keywords'])}, relaxation sounds, ambient music, nature therapy, sound therapy, peaceful sounds, calming sounds, tranquil sounds, zen sounds, meditation sounds, yoga sounds, spa sounds, massage sounds, healing sounds, therapeutic sounds, natural sounds, outdoor sounds, wilderness sounds, relaxation music, ambient sounds, background sounds, study sounds, sleep sounds, ASMR, white noise, focus sounds, concentration sounds, mindfulness sounds, stress relief sounds, anxiety relief sounds, peaceful music, calming music, soothing sounds, nature ambience

---

© 2026 Soooth - AI-Generated Soothing Nature Videos
Generated with ❤️ using advanced AI and nature sound design

#NatureSounds #{theme_label.replace(' ', '')} #Relaxation #Sleep #Meditation #Study #Focus #StressRelief #Anxiety #ASMR #WhiteNoise #Ambience #Calming #Peaceful #Wellness #SelfCare #MentalHealth #Mindfulness #Tranquility #Serenity #InnerPeace"""

    # Comprehensive SEO tags (YouTube allows up to 500 characters total)
    tags = [
        # Primary keywords
        f"{theme_label.lower()} sounds",
        f"{theme_label.lower()} ambience",
        "nature sounds",
        "relaxation",
        "sleep sounds",
        "meditation music",
        "study music",

        # Theme-specific
        *theme_info['keywords'],

        # Popular search terms
        "calming sounds",
        "stress relief",
        "anxiety relief",
        "deep sleep",
        "insomnia relief",
        "focus music",
        "concentration",
        "peaceful",
        "tranquil",
        "soothing",

        # ASMR & trending
        "ASMR",
        "white noise",
        "ambient music",
        "background sounds",
        "sound therapy",

        # Duration-based
        f"{duration_minutes} minutes",
        "long duration" if duration_minutes >= 30 else "short duration",

        # Use cases
        "sleep aid",
        "study ambience",
        "work music",
        "yoga music",
        "spa music",
        "massage music",

        # Wellness
        "mental health",
        "self care",
        "wellness",
        "mindfulness",
        "zen",
    ]

    # Limit tags to fit within YouTube's 500 character limit
    tags_str = ','.join(tags)
    if len(tags_str) > 450:
        tags = tags[:30]  # Trim to first 30 tags

    return {
        "title": title,
        "description": description,
        "tags": tags,
    }


def upload_to_youtube(
    video_path: str,
    title: str = None,
    description: str = None,
    tags: list[str] = None,
    theme: str = "forest",
    duration_minutes: int = 1,
    category_id: str = "22",  # 22 = People & Blogs (or use 10 for Music)
    privacy: str = "public",
) -> str:
    """Upload a video to YouTube with full SEO optimization and return the video ID."""

    # Always generate SEO-optimized metadata (can be overridden with custom values)
    logger.info(f"Generating SEO metadata for theme={theme}, duration={duration_minutes}min")
    seo_data = generate_seo_optimized_metadata(theme, duration_minutes)

    # Use provided values if explicitly set, otherwise use SEO-generated
    logger.info(f"Input: title={title}, description={description}, tags={tags}")
    if not title:
        title = seo_data["title"]
        logger.info(f"Using SEO title: {title}")
    if not description:
        description = seo_data["description"]
        logger.info(f"Using SEO description (first 100 chars): {description[:100]}...")
    if not tags:
        tags = seo_data["tags"]
        logger.info(f"Using SEO tags: {len(tags)} tags")

    logger.info(f"Final upload title: {title}")

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10",  # Music category for better discoverability
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
            "publishAt": None,  # Publish immediately
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    logger.info(f"Upload complete! Video ID: {video_id}")
    return video_id
