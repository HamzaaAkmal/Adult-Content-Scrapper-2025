# 🎵 NSFW Audio Dataset Scraper

An intelligent, fully autonomous Streamlit-based web scraper that extracts NSFW audio clips from video content using AI-powered classification with Groq's Whisper model.

## 🌟 Features

### Smart Web Crawling
- **Auto-discovery**: Automatically crawls websites to find video content
- **Pattern detection**: Identifies video URLs using HTML parsing and keyword matching
- **Multi-format support**: Handles MP4, WebM, AVI, MOV, MKV, and embedded videos
- **Concurrent processing**: Scrapes up to 10 websites simultaneously

### AI-Powered Classification
- **Groq Whisper Integration**: Uses `whisper-large-v3-turbo` for accurate transcription
- **NSFW Detection**: Identifies 6 categories of NSFW audio content:
  - Moaning
  - Heavy breathing
  - Explicit language
  - Dirty talk
  - Orgasm sounds
  - Roleplay
- **Confidence scoring**: Only extracts clips with ≥70% confidence

### Intelligent Clip Extraction
- **Precise timing**: Extracts exactly 10-second clips around NSFW timestamps
- **Multiple clips**: Up to 3 clips per video
- **Auto-organization**: Files organized by category and source domain
- **Rich metadata**: JSON metadata for each clip with timestamps, confidence, and categories

### User-Friendly Interface
- **Clean Streamlit UI**: Simple CSV upload interface
- **Real-time progress**: Live updates on scraping progress
- **Statistics dashboard**: Visualize clips by category and domain
- **One-click download**: Get all clips and metadata in a ZIP file

## 📋 Requirements

### System Dependencies
```bash
# Install FFmpeg (required for audio processing)
# Windows (using Chocolatey):
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Additional Tools
- **yt-dlp**: Auto-installed via pip for video downloading
- **Python 3.8+**: Required

## 🚀 Quick Start

### 1. Installation
```bash
cd streamlit_scraper
pip install -r requirements.txt
```

### 2. Prepare CSV File
Create a CSV file with website URLs. Example (`websites.csv`):
```csv
url
https://example1.com
https://example2.com
https://example3.com
```

The scraper auto-detects the URL column (supports any column name containing "url" or "link").

### 3. Run the Application
```bash
streamlit run app.py
```

### 4. Use the Interface
1. Upload your CSV file
2. Review the detected URLs
3. Click "Start Scraping"
4. Monitor progress in real-time
5. Download the ZIP file with extracted clips

## 📁 Output Structure

```
streamlit_scraper/
├── clips/
│   ├── moaning/
│   │   ├── example.com/
│   │   │   ├── clip_20240114_120000_0.mp3
│   │   │   ├── clip_20240114_120000_0.json
│   │   │   └── ...
│   ├── explicit_language/
│   ├── dirty_talk/
│   └── ...
├── metadata/
│   └── master_metadata.json
└── temp/
```

### Metadata Format
Each clip includes a JSON file:
```json
{
  "url": "https://example.com/video",
  "domain": "example.com",
  "timestamp": 45.2,
  "duration": 10,
  "category": "moaning",
  "all_categories": ["moaning", "heavy_breathing"],
  "confidence": 0.89,
  "text": "transcribed audio content...",
  "clip_path": "moaning/example.com/clip_xxx.mp3",
  "extracted_at": "2024-01-14T12:00:00"
}
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# API Configuration
GROQ_API_KEY = "your_api_key_here"

# Scraping Settings
MAX_CONCURRENT_SCRAPES = 10
MIN_VIDEO_DURATION = 10  # seconds
MAX_CLIPS_PER_VIDEO = 3
CLIP_DURATION = 10  # seconds

# Detection Threshold
MIN_CONFIDENCE = 0.7
```

## 🎯 How It Works

### Pipeline Flow
```
CSV URLs → Web Crawler → Video Discovery → Download
                                               ↓
                                          Extract Audio
                                               ↓
                                       Whisper Transcription
                                               ↓
                                         NSFW Classification
                                               ↓
                                      Extract 10s Clips
                                               ↓
                                   Organize by Category
                                               ↓
                                      Generate Metadata
                                               ↓
                                        Create ZIP
```

### NSFW Detection Logic
1. **Transcription**: Groq Whisper converts audio to text with timestamps
2. **Keyword matching**: Checks for explicit words and phrases
3. **Pattern detection**: Identifies vocal patterns (moaning, breathing)
4. **Confidence scoring**: Calculates probability based on multiple factors
5. **Category assignment**: Tags clips with relevant NSFW categories

## 🛡️ Edge Case Handling

The scraper automatically handles:
- **Invalid URLs**: Skips and logs errors
- **Failed downloads**: Tries yt-dlp, then falls back to direct download
- **Short videos**: Filters out videos under 10 seconds
- **No NSFW content**: Skips videos with no detected NSFW audio
- **API failures**: Gracefully handles Whisper API errors
- **Rate limiting**: Implements delays to avoid overwhelming servers
- **File size limits**: Skips videos over 500MB
- **Timeouts**: Sets reasonable timeouts for all operations

## 📊 Performance

- **Concurrent scraping**: 10 websites processed simultaneously
- **Async operations**: Non-blocking I/O for maximum efficiency
- **Smart caching**: Avoids re-crawling visited URLs
- **Resource cleanup**: Automatically removes temporary files

## 🔒 API Key Security

The Groq API key is currently hardcoded in `config.py`. For production use:

1. Create a `.env` file:
```env
GROQ_API_KEY=gsk_your_api_key_here
```

2. Update `config.py`:
```python
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
```

## 🐛 Troubleshooting

### FFmpeg not found
```bash
# Verify installation
ffmpeg -version
ffprobe -version

# Add to PATH if needed
```

### yt-dlp errors
```bash
# Update yt-dlp
pip install --upgrade yt-dlp
```

### Whisper API errors
- Check API key validity
- Verify internet connection
- Check Groq API status

### No clips extracted
- Ensure videos contain audio
- Check confidence threshold (try lowering MIN_CONFIDENCE)
- Review Whisper transcription output in logs

## 📝 Example Usage

```python
# Programmatic usage (without Streamlit)
import asyncio
from scraper_pipeline import run_scraper

urls = [
    "https://example1.com",
    "https://example2.com"
]

results = asyncio.run(run_scraper(urls))
print(f"Extracted {results['clips_extracted']} clips")
```

## 🔄 Updates & Maintenance

- **yt-dlp**: Update regularly for compatibility with new sites
- **Groq API**: Monitor for model updates or API changes
- **Dependencies**: Keep Python packages up to date

## 📜 License

This tool is for research and dataset creation purposes. Ensure compliance with:
- Website terms of service
- Content licensing and copyright laws
- Local regulations regarding adult content
- API usage policies

## 🤝 Contributing

To enhance the scraper:
1. Add more NSFW detection patterns
2. Improve video discovery algorithms
3. Support additional video platforms
4. Optimize performance

## ⚠️ Disclaimer

This tool is designed for legitimate dataset creation and research purposes. Users are responsible for:
- Respecting website terms of service
- Ensuring legal compliance
- Obtaining necessary permissions
- Ethical use of extracted content

---

**Built with**: Python, Streamlit, Groq Whisper, FFmpeg, yt-dlp, BeautifulSoup

**Version**: 1.0.0

**Support**: For issues or questions, check the logs in the Streamlit interface or review error messages in the console.
