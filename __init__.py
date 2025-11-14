"""
NSFW Audio Dataset Scraper

An intelligent, fully autonomous web scraper that extracts NSFW audio clips
from video content using AI-powered classification with Groq's Whisper model.

Modules:
    - config: Configuration settings
    - web_crawler: Intelligent website crawling for video discovery
    - video_downloader: Video downloading with yt-dlp and fallback
    - whisper_classifier: NSFW audio classification using Groq Whisper
    - clip_extractor: Audio clip extraction and organization
    - scraper_pipeline: Main orchestration pipeline
    - app: Streamlit web interface

Usage:
    # Via Streamlit UI:
    streamlit run app.py
    
    # Programmatically:
    from scraper_pipeline import run_scraper
    import asyncio
    
    urls = ["https://example.com"]
    results = asyncio.run(run_scraper(urls))
"""

__version__ = "1.0.0"
__author__ = "NSFW Scraper Team"

from .scraper_pipeline import NSFWScraper, run_scraper
from .config import NSFW_CATEGORIES, MIN_CONFIDENCE

__all__ = [
    'NSFWScraper',
    'run_scraper',
    'NSFW_CATEGORIES',
    'MIN_CONFIDENCE'
]
