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
MAX_CONCURRENT_SCRAPES = 5  # Reduced for better quality control
MIN_VIDEO_DURATION = 15  # seconds - longer videos for better content
MAX_CLIPS_PER_VIDEO = 3  # Extract fewer, higher quality clips per video
CLIP_DURATION = 10  # seconds - standard clip length

# Dataset Balancing Configuration
MAX_CLIPS_PER_CATEGORY = 100  # Maximum 100 MP3s per category for balanced dataset

# Quality Control for Training Data
MIN_AUDIO_BITRATE = 128  # kbps - minimum audio quality
MIN_SAMPLE_RATE = 44100  # Hz - CD quality audio
REQUIRE_STEREO = False  # Require stereo audio (can be False for flexibility)

# NSFW Categories - Streamlined for high-quality balanced training data
NSFW_CATEGORIES = [
    # Primary Vocal Categories (Core)
    "moaning",
    "heavy_breathing",
    "screaming",
    "gasping",
    
    # Language Categories (Core)
    "explicit_language",
    "dirty_talk",
    "begging",
    
    # Activity Categories (Core)
    "orgasm_sounds",
    "pleasure_sounds",
    "kissing_sounds"
]

# NSFW Detection Keywords - Comprehensive multilingual keywords for accurate classification
NSFW_KEYWORDS = {
    # Primary Vocal
    "moaning": [
        # English
        "moan", "moaning", "mmm", "mmmm", "ahh", "ahhh", "ohh", "ohhh", "unh", "ungh", 
        "ugh", "mmph", "ngh", "nghhh", "ooh", "oooh", "aah", "aaah", "hmmm", "mmhm",
        "oh yeah", "oh yes", "yeah baby", "mm yeah", "uh huh", "oh my", "mmm yeah",
        # Variations
        "ah ah ah", "oh oh oh", "uh uh uh", "mm mm mm", "moans", "moan loudly",
        "soft moan", "loud moan", "quiet moan", "gentle moan", "deep moan"
    ],
    
    "heavy_breathing": [
        # English
        "panting", "pant", "pants", "breathing heavy", "heavy breathing", "out of breath", 
        "breathe", "breathing", "huff", "huffing", "puff", "puffing", "wheeze", "wheezing",
        "breathless", "catching breath", "short breath", "rapid breathing", "fast breathing",
        # Phonetic
        "hah", "hah hah", "huh", "huh huh", "haah", "huuh", "phew", "hff", "hff hff",
        # Descriptions
        "can't breathe", "breath fast", "breath hard", "breathing faster", "breathing harder"
    ],
    
    "screaming": [
        # English
        "scream", "screaming", "screams", "yell", "yelling", "yells", "shriek", "shrieking",
        "aaah", "aaaaah", "aaahh", "eeeek", "ahhhhh", "ohhhh", "screech", "screeching",
        # Variations
        "loud scream", "scream loud", "screaming loud", "oh my god", "oh god", "omg",
        "holy shit", "jesus", "christ", "fuck yes", "oh fuck", "fucking scream"
    ],
    
    "gasping": [
        # English
        "gasp", "gasping", "gasps", "gulp", "gulping", "choke", "choking", "breathless",
        # Phonetic
        "hah", "huh", "gah", "guh", "ahh", "*gasp*", "*gulp*", "haah", "huuh",
        # Descriptions
        "sharp breath", "sudden breath", "quick breath", "catch breath", "air gasp",
        "surprised gasp", "shocked gasp", "deep gasp", "loud gasp"
    ],
    
    # Language - Explicit
    "explicit_language": [
        # Core profanity
        "fuck", "fucking", "fucked", "fucker", "fucks", "fuckin", "fck", "f*ck",
        "shit", "shitting", "shits", "bullshit", "shitty", "holy shit",
        "cock", "cocks", "dick", "dicks", "penis", "prick", "dong",
        "pussy", "pussies", "cunt", "cunts", "vagina", "coochie", "kitty",
        "ass", "asses", "asshole", "assholes", "butt", "butthole", "arse",
        "bitch", "bitches", "bitching", "son of a bitch", "bastard", "bastards",
        "slut", "sluts", "slutty", "whore", "whores", "hoe", "ho",
        # Combinations
        "fuck me", "fucking hell", "what the fuck", "holy fuck", "fuck yeah",
        "ass fuck", "fuck my ass", "fuck my pussy", "fucking pussy", "tight pussy",
        "wet pussy", "pussy so wet", "cock so hard", "hard cock", "big cock", "huge cock",
        "suck my cock", "suck my dick", "eat my pussy", "lick my pussy",
        # Crude terms
        "titties", "tits", "boobs", "boobies", "breasts", "nipples", "nipple",
        "balls", "testicles", "nuts", "ballsack", "cum", "jizz", "sperm", "load",
        "damn", "damned", "goddamn", "god damn", "bloody hell", "crap", "piss"
    ],
    
    # Language - Dirty Talk
    "dirty_talk": [
        # Commands/requests
        "daddy", "baby", "babe", "sweetheart", "harder", "faster", "deeper", "slower",
        "right there", "just like that", "keep going", "don't stop", "more", "give me more",
        # Sexual language
        "fuck me", "fuck me hard", "fuck me harder", "fuck me faster", "fuck me deeper",
        "make me", "make me cum", "make me scream", "make me yours", "take me",
        "i'm yours", "all yours", "use me", "have me", "want you", "need you",
        "want your cock", "need your cock", "want you inside", "need you inside",
        # Descriptions
        "so hard", "so big", "so deep", "so good", "feels good", "feel you",
        "so wet", "wet for you", "dripping", "dripping wet", "soaking wet",
        "so tight", "tight pussy", "tight ass", "stretch me", "fill me", "fill me up",
        "your cock feels", "your dick feels", "inside me", "deep inside", "balls deep",
        # Intensity
        "pound me", "drill me", "ram me", "slam into me", "thrust", "thrusting",
        "rough", "be rough", "rough with me", "treat me rough", "manhandle me",
        # Affirmations
        "yes daddy", "yes baby", "yes sir", "oh yes", "god yes", "fuck yes",
        "yeah baby", "that's it", "perfect", "amazing", "incredible", "so fucking good"
    ],
    
    # Language - Begging
    "begging": [
        # Please variations
        "please", "plz", "pls", "pretty please", "please please", "please baby",
        "please daddy", "please sir", "oh please", "god please",
        # Don't stop
        "don't stop", "please don't stop", "never stop", "keep going", "don't you dare stop",
        "don't you stop", "can't stop", "won't stop", "no stopping",
        # Need/want
        "need", "need you", "need it", "need you so bad", "need you inside",
        "want", "want you", "want it", "want you so bad", "want you inside",
        "i want", "i need", "i want you", "i need you", "gotta have you",
        # Begging phrases
        "beg", "begging", "i'm begging", "begging for it", "begging you",
        "let me", "let me have it", "give it to me", "give me", "give me more",
        "i'll do anything", "anything you want", "whatever you want",
        # Desperate
        "desperate", "so desperate", "dying for it", "craving", "crave you",
        "starving", "hungry for you", "thirsty", "aching", "aching for you"
    ],
    
    # Activity - Orgasm
    "orgasm_sounds": [
        # Cumming variations
        "cumming", "i'm cumming", "gonna cum", "about to cum", "going to cum",
        "cum", "coming", "i'm coming", "gonna come", "about to come",
        "make me cum", "cum for you", "cum inside", "cum in me", "cum on me",
        # Orgasm
        "orgasm", "orgasming", "having an orgasm", "multiple orgasms",
        # Expressions
        "yes yes yes", "yes yes", "oh god", "oh my god", "oh fuck",
        "holy fuck", "jesus christ", "oh jesus", "god yes", "fuck yes",
        "don't stop", "right there", "keep going", "just like that",
        # Intensity
        "so close", "almost there", "getting close", "about to explode",
        "gonna explode", "can't hold it", "can't take it", "too much",
        "so good", "feels so good", "best ever", "never felt", "incredible",
        # Climax
        "climax", "climaxing", "peak", "edge", "edging", "finish", "finishing"
    ],
    
    # Activity - Pleasure
    "pleasure_sounds": [
        # Feels good
        "feels good", "feel good", "feels so good", "feeling so good",
        "feels great", "feels amazing", "feels incredible", "feels wonderful",
        "so good", "really good", "very good", "too good", "damn good",
        # Love it
        "love it", "love this", "love that", "loving it", "i love",
        "love how you", "love when you", "love your", "absolutely love",
        # Like it
        "like that", "like this", "just like that", "right like that",
        "i like", "like it when", "like how you", "like your",
        # Right there
        "right there", "yes right there", "there", "that's it", "that's the spot",
        "perfect spot", "hit the spot", "sweet spot", "g spot", "good spot",
        # Enjoyment
        "enjoy", "enjoying", "enjoy this", "enjoy that", "pleasure",
        "pleasurable", "satisfying", "satisfied", "heaven", "heavenly",
        "bliss", "blissful", "ecstasy", "euphoria", "divine",
        # Positive affirmations
        "amazing", "incredible", "wonderful", "fantastic", "awesome",
        "spectacular", "phenomenal", "outstanding", "unbelievable", "best ever",
        "never felt this", "never felt so", "best feeling", "best i've ever"
    ],
    
    # Activity - Kissing
    "kissing_sounds": [
        # Kissing
        "kissing", "kiss", "kisses", "kissed", "kiss me", "kissing me",
        "kissing you", "make out", "making out", "makeout",
        # Phonetic sounds
        "muah", "mwah", "mwuah", "smooch", "smooching", "smack",
        "*kiss*", "*smooch*", "chu", "mmm kiss", "mmwah",
        # Descriptions
        "soft kiss", "gentle kiss", "tender kiss", "passionate kiss",
        "deep kiss", "french kiss", "tongue kiss", "wet kiss",
        "kiss my lips", "kiss my neck", "kiss my body", "kiss me there",
        "lips", "lipstick", "your lips", "my lips", "our lips",
        # Intimate
        "passionate", "passion", "romantic", "romance", "intimate", "intimacy",
        "tender", "tenderly", "gently", "softly", "sweet", "sweetly"
    ]
}

# Confidence Threshold - High threshold for accurate classification
MIN_CONFIDENCE = 0.88  # 88% confidence required for high accuracy
MIN_KEYWORD_MATCHES = 2  # Require at least 2 keyword matches per clip to avoid false positives
MIN_SEGMENT_LENGTH = 3  # Minimum segment length in words for context

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
