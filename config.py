"""Configuration settings for the NSFW audio scraper."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found! Please:\n"
        "1. Copy .env.example to .env\n"
        "2. Add your Groq API key to .env\n"
        "Get your key from: https://console.groq.com/keys"
    )

GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"

# Scraping Configuration
MAX_CONCURRENT_SCRAPES = 10
MIN_VIDEO_DURATION = 10  # seconds
MAX_CLIPS_PER_VIDEO = 3
CLIP_DURATION = 10  # seconds

# NSFW Categories
NSFW_CATEGORIES = [
    "moaning",
    "heavy_breathing",
    "explicit_language",
    "dirty_talk",
    "orgasm_sounds",
    "roleplay"
]

# NSFW Detection Keywords
NSFW_KEYWORDS = {
    "moaning": ["moan", "mmm", "ahh", "ohh", "unh", "ugh"],
    "heavy_breathing": ["breath", "pant", "gasp", "huff"],
    "explicit_language": ["fuck", "shit", "cock", "pussy", "ass", "dick", "bitch", "damn"],
    "dirty_talk": ["daddy", "baby", "harder", "deeper", "faster", "cum", "wet", "tight"],
    "orgasm_sounds": ["cumming", "orgasm", "yes yes", "oh god", "don't stop"],
    "roleplay": ["master", "slave", "sir", "mistress", "submit", "obey"]
}

# Confidence Threshold
MIN_CONFIDENCE = 0.7

# Video Detection Patterns
VIDEO_KEYWORDS = [
    "video", "media", "player", "mp4", "watch", "embed", "stream",
    "clip", "movie", "play", "content", "thumb", "preview"
]
VIDEO_EXTENSIONS = [".mp4", ".webm", ".avi", ".mov", ".mkv", ".flv", ".m3u8", ".mpd", ".ts"]

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Ensure directories exist
for directory in [CLIPS_DIR, METADATA_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
