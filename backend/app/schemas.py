from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import random


# Study Babe Variations for diversity and variety
STUDY_BABE_VARIATIONS = {
    "ethnicity": [
        "elegant Asian woman with sleek straight black hair",
        "beautiful European woman with long wavy blonde hair",
        "stunning African woman with natural curly hair",
        "gorgeous Latina woman with flowing dark brown hair",
        "graceful Middle Eastern woman with long wavy black hair",
        "sophisticated South Asian woman with silky dark hair",
        "striking Eastern European woman with auburn wavy hair",
        "captivating Mediterranean woman with brunette curls"
    ],
    "outfit": [
        "luxurious deep blue silk blouse with white pants",
        "elegant burgundy velvet dress",
        "sophisticated emerald green satin shirt with black skirt",
        "glamorous gold sequined top with cream trousers",
        "chic crimson silk wrap blouse with tailored pants",
        "stunning navy blue designer blazer with silk camisole",
        "opulent purple satin shirt with high-waisted pants",
        "refined ivory silk blouse with charcoal grey slacks",
        "dazzling champagne-colored satin dress",
        "classy rose gold metallic top with elegant skirt"
    ],
    "setting": [
        "grand historical library with ornate wooden bookshelves reaching to the ceiling",
        "luxurious modern penthouse study with floor-to-ceiling windows and city skyline views",
        "opulent baroque palace room with crystal chandeliers and gilded furniture",
        "sophisticated art deco mansion study with geometric patterns and brass accents",
        "elegant Victorian library with mahogany furniture and velvet curtains",
        "glamorous contemporary loft with exposed brick walls and designer furniture",
        "majestic Renaissance-style study with marble columns and frescoed ceilings",
        "chic Parisian apartment with ornate moldings and French windows",
        "lavish Hollywood Regency room with mirrored surfaces and plush furnishings",
        "stunning minimalist modern space with marble and gold accents"
    ],
    "atmosphere": [
        "warm amber lighting creating dramatic shadows",
        "soft golden hour sunlight streaming through windows",
        "elegant candlelight with sparkling highlights",
        "bright natural daylight with gentle bokeh effects",
        "moody dramatic lighting with rich warm tones",
        "dreamy backlit glow with lens flares",
        "sophisticated studio lighting with artistic shadows",
        "romantic sunset lighting with golden hues"
    ]
}

def get_random_study_babe_prompt():
    """Generate a random varied Study Babe video prompt with diversity."""
    ethnicity = random.choice(STUDY_BABE_VARIATIONS["ethnicity"])
    outfit = random.choice(STUDY_BABE_VARIATIONS["outfit"])
    setting = random.choice(STUDY_BABE_VARIATIONS["setting"])
    atmosphere = random.choice(STUDY_BABE_VARIATIONS["atmosphere"])

    prompt = f"Cinematic portrait of an {ethnicity}, wearing {outfit}, sitting in a {setting}, working on a laptop, surrounded by books and elegant decor, {atmosphere}, sophisticated and glamorous atmosphere, shallow depth of field, professional fashion photography, ultra high quality 4K, rich color palette, artistic composition, no text"

    return prompt

THEME_PROMPTS = {
    "forest": {
        "video": "Slow cinematic drone shot gliding over a misty ancient forest at golden sunrise, soft light rays filtering through towering trees, gentle fog rolling between trunks, 4K nature footage, peaceful serene atmosphere, no text no people",
        "music": "Gentle ambient instrumental with soft piano melody and warm string pads, forest-inspired, peaceful and meditative, slow tempo 60bpm, no vocals",
    },
    "ocean": {
        "video": "Calm turquoise ocean waves gently rolling onto pristine white sand beach at sunset, golden hour light reflecting on water surface, aerial cinematic view, 4K nature footage, tranquil peaceful atmosphere, no text no people",
        "music": "Soothing ambient instrumental with soft synthesizer pads and gentle harp arpeggios, ocean-inspired, calming and relaxing, slow tempo 55bpm, no vocals",
    },
    "rain": {
        "video": "Gentle rain falling on lush green leaves in a tropical garden, close-up droplets sliding down leaves, soft diffused natural light, cinematic macro nature footage, 4K peaceful atmosphere, no text no people",
        "music": "Calm lo-fi ambient instrumental with soft piano chords and warm pad textures, rain-inspired, cozy and contemplative, slow tempo 65bpm, no vocals",
    },
    "mountain": {
        "video": "Majestic snow-capped mountain peaks emerging above clouds at sunrise, slow cinematic aerial pan, golden light painting the summits, vast pristine wilderness, 4K nature footage, awe-inspiring peaceful, no text no people",
        "music": "Expansive ambient instrumental with ethereal synthesizer drones and gentle flute melody, mountain-inspired, grand yet peaceful, slow tempo 50bpm, no vocals",
    },
    "meadow": {
        "video": "Endless wildflower meadow swaying gently in warm breeze, butterflies floating among colorful blossoms, soft golden afternoon sunlight, slow cinematic dolly shot, 4K nature footage, idyllic peaceful, no text no people",
        "music": "Light acoustic ambient instrumental with soft guitar fingerpicking and gentle wind chimes, meadow-inspired, cheerful and serene, slow tempo 70bpm, no vocals",
    },
    "starry_night": {
        "video": "Crystal clear night sky filled with millions of stars and visible Milky Way galaxy, slow rotation timelapse over silhouetted mountain landscape, faint aurora borealis on horizon, 4K nature footage, magical peaceful, no text no people",
        "music": "Deep space ambient instrumental with soft evolving synthesizer textures and gentle celestial bells, night sky inspired, dreamy and vast, very slow tempo 45bpm, no vocals",
    },
    "study_babe": {
        "video": get_random_study_babe_prompt(),  # This will be replaced dynamically in the router
        "music": "Lo-fi study beats instrumental with warm piano chords, soft vinyl crackle, gentle jazzy Rhodes keys, dreamy ambient pads, calm and focused atmosphere, slow tempo 72bpm, no vocals",
    },
}


class GenerateRequest(BaseModel):
    theme: str = "forest"
    video_source: str = "ai"  # "ai" or "stock"
    upload_youtube: bool = False
    no_audio: bool = False
    custom_video_prompt: Optional[str] = None
    custom_music_prompt: Optional[str] = None
    duration: int = 60
    batch_count: int = 1  # Number of videos to generate in batch


class JobResponse(BaseModel):
    id: str
    status: str
    theme: str
    duration: int
    youtube_id: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]


class BatchJobResponse(BaseModel):
    jobs: list[JobResponse]
    batch_count: int
