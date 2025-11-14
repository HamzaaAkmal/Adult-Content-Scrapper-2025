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
MIN_VIDEO_DURATION = 12  # seconds - balanced video length requirement
MAX_CLIPS_PER_VIDEO = 4  # Extract moderate clips per video for training data
CLIP_DURATION = 12  # seconds - balanced clips for good context

# Quality Control for Training Data
MIN_AUDIO_BITRATE = 128  # kbps - minimum audio quality
MIN_SAMPLE_RATE = 44100  # Hz - CD quality audio
REQUIRE_STEREO = False  # Require stereo audio (can be False for flexibility)

# NSFW Categories - Expanded for comprehensive training data
NSFW_CATEGORIES = [
    # Primary Vocal Categories
    "moaning",
    "heavy_breathing",
    "screaming",
    "whimpering",
    "gasping",
    
    # Language Categories
    "explicit_language",
    "dirty_talk",
    "sexual_commands",
    "begging",
    
    # Activity Categories
    "orgasm_sounds",
    "pleasure_sounds",
    "pain_pleasure",
    "kissing_sounds",
    "sucking_sounds",
    
    # Roleplay Categories
    "roleplay",
    "dominance",
    "submission",
    "degradation",
    
    # Other
    "body_slapping",
    "wet_sounds",
    "intense_activity"
]

# NSFW Detection Keywords - Comprehensive for accurate classification
NSFW_KEYWORDS = {
    # Primary Vocal
    "moaning": ["moan", "mmm", "ahh", "ohh", "unh", "ugh", "mmph", "ngh"],
    "heavy_breathing": ["breath", "pant", "gasp", "huff", "puff", "wheeze"],
    "screaming": ["scream", "yell", "shriek", "aaah", "oh my god"],
    "whimpering": ["whimper", "whine", "sob", "cry", "please"],
    "gasping": ["gasp", "gulp", "choke", "breathless"],
    
    # Language
    "explicit_language": ["fuck", "shit", "cock", "pussy", "ass", "dick", "bitch", "damn", "cunt", "slut", "whore"],
    "dirty_talk": ["daddy", "baby", "harder", "deeper", "faster", "cum", "wet", "tight", "hot", "sexy"],
    "sexual_commands": ["suck", "lick", "ride", "bend over", "take it", "open wide", "spread"],
    "begging": ["please", "beg", "need", "want", "give me", "let me"],
    
    # Activity
    "orgasm_sounds": ["cumming", "orgasm", "yes yes", "oh god", "don't stop", "i'm coming"],
    "pleasure_sounds": ["feels good", "so good", "amazing", "incredible", "love it"],
    "pain_pleasure": ["hurts", "pain", "rough", "hurt me", "spank"],
    "kissing_sounds": ["kiss", "muah", "smooch", "lips"],
    "sucking_sounds": ["suck", "slurp", "gulp", "swallow"],
    
    # Roleplay
    "roleplay": ["master", "slave", "sir", "mistress", "submit", "obey", "stepbrother", "stepsis"],
    "dominance": ["master", "dom", "control", "command", "own", "dominate"],
    "submission": ["slave", "submit", "serve", "obey", "yes sir", "yes master"],
    "degradation": ["slut", "whore", "bitch", "dirty", "filthy", "nasty"],
    
    # Other
    "body_slapping": ["slap", "spank", "smack", "hit", "clap"],
    "wet_sounds": ["wet", "drip", "squish", "splash", "moist"],
    "intense_activity": ["pound", "thrust", "ram", "drill", "intense"]
}

# Confidence Threshold - Medium threshold for balanced training data
MIN_CONFIDENCE = 0.85  # 85% confidence required for balanced quality/quantity
MIN_KEYWORD_MATCHES = 1  # Require at least 1 keyword match per clip
MIN_SEGMENT_LENGTH = 2  # Minimum segment length in words

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
