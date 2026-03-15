from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
        "video": "Full body shot of a stunningly gorgeous young woman model with athletic fuller curvy figure, perfect skin, soft delicate facial features, wavy flowing hair, captivating eyes looking directly at camera with gentle alluring expression, golden hour warm sunlight illuminating her face and hair, sitting at a dreamy aesthetic desk studying, wearing elegant stylish outfit, surrounded by books and notes, stunning unreal fantasy landscape visible through large window, ethereal clouds and floating islands outside, shallow depth of field, cinematic portrait photography style, cozy magical atmosphere, 4K cinematic, no text",
        "music": "Lo-fi study beats instrumental with warm piano chords, soft vinyl crackle, gentle jazzy Rhodes keys, dreamy ambient pads, calm and focused atmosphere, slow tempo 72bpm, no vocals",
    },
}


class GenerateRequest(BaseModel):
    theme: str = "forest"
    video_source: str = "ai"  # "ai" or "stock"
    custom_video_prompt: Optional[str] = None
    custom_music_prompt: Optional[str] = None
    duration: int = 60


class JobResponse(BaseModel):
    id: str
    status: str
    theme: str
    duration: int
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
