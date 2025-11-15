"""
Streamlit YouTube Safe Audio Scraper
Interactive web interface for downloading safe audio from YouTube and creating zip archives
"""

import streamlit as st
import os
import subprocess
from pathlib import Path
import time
import zipfile
from datetime import datetime
import threading
import queue

# Configuration
OUTPUT_DIR = r"c:\Users\Hamza\Desktop\NSFW Voice Dataset\binary training data\safe"
TEMP_DIR = r"c:\Users\Hamza\Desktop\NSFW Voice Dataset\temp_downloads"
ZIP_DIR = r"c:\Users\Hamza\Desktop\NSFW Voice Dataset\zipped_datasets"
SAMPLE_RATE = 16000
DURATION = 10  # seconds
TARGET_COUNT = 800  # total files
VIDEOS_PER_CATEGORY = 10  # Videos per category

# 8 Safe Categories
CATEGORIES = {
    "podcast": "🎙️ Podcast",
    "educational": "📚 Educational",
    "music_instrumental": "🎵 Music",
    "news": "📰 News",
    "conversation": "💬 Conversation",
    "nature": "🌿 Nature",
    "audiobook": "📖 Audiobook",
    "meditation": "🧘 Meditation"
}

# YouTube Videos (80 videos total - 10 per category)
SAFE_VIDEOS = {
    "podcast": [
        "https://www.youtube.com/watch?v=PMotykw0SIk",
        "https://www.youtube.com/watch?v=ycPr5-27vSI",
        "https://www.youtube.com/watch?v=BpBnJq19R60",
        "https://www.youtube.com/watch?v=6YLTLRxK5m8",
        "https://www.youtube.com/watch?v=1YbcB6b4A2U",
        "https://www.youtube.com/watch?v=aJX4ytfqw6k",
        "https://www.youtube.com/watch?v=MA4jJNlMiPo",
        "https://www.youtube.com/watch?v=MdZAMSyn_As",
        "https://www.youtube.com/watch?v=4kDyBqhXHLY",
        "https://www.youtube.com/watch?v=lI9Ri92N3wA",
    ],
    "educational": [
        "https://www.youtube.com/watch?v=yaqe1qesQ8c",
        "https://www.youtube.com/watch?v=IvUU8joBb1Q",
        "https://www.youtube.com/watch?v=xuCn8ux2gbs",
        "https://www.youtube.com/watch?v=1RWOpQXTltA",
        "https://www.youtube.com/watch?v=wJa5Ch0O4BI",
        "https://www.youtube.com/watch?v=nvTee3ZRNZw",
        "https://www.youtube.com/watch?v=UuRxRGR3VpM",
        "https://www.youtube.com/watch?v=DxREm3s1scA",
        "https://www.youtube.com/watch?v=OMKVpCCQ1Ng",
        "https://www.youtube.com/watch?v=3DZbSlkFoSU",
    ],
    "music_instrumental": [
        "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "https://www.youtube.com/watch?v=5qap5aO4i9A",
        "https://www.youtube.com/watch?v=DWcJFNfaw9c",
        "https://www.youtube.com/watch?v=lTRiuFIWV54",
        "https://www.youtube.com/watch?v=36YnV9STBqc",
        "https://www.youtube.com/watch?v=hHW1oY26kxQ",
        "https://www.youtube.com/watch?v=_tV5LEBDs7w",
        "https://www.youtube.com/watch?v=2OEL4P1Rz04",
        "https://www.youtube.com/watch?v=M5QY2_8704o",
        "https://www.youtube.com/watch?v=n61ULEU7CO0",
    ],
    "nature": [
        "https://www.youtube.com/watch?v=eKFTSSKCzWA",
        "https://www.youtube.com/watch?v=qYnA9wWFHLI",
        "https://www.youtube.com/watch?v=bIiRtWGkP2g",
        "https://www.youtube.com/watch?v=McIDY9vdBHA",
        "https://www.youtube.com/watch?v=3sL0omwElxw",
        "https://www.youtube.com/watch?v=i2aAGPzPF7Y",
        "https://www.youtube.com/watch?v=UfcAVejslrU",
        "https://www.youtube.com/watch?v=CsSgg_iXj34",
        "https://www.youtube.com/watch?v=bNyUyrR0PHo",
        "https://www.youtube.com/watch?v=lDi9uFcD7XI",
    ],
    "news": [
        "https://www.youtube.com/watch?v=DkGMY63FF3Q",
        "https://www.youtube.com/watch?v=f2vNuaBQNGU",
        "https://www.youtube.com/watch?v=3Q3PSISAZL8",
        "https://www.youtube.com/watch?v=HAnw168huqA",
        "https://www.youtube.com/watch?v=1WQlKJfxHT0",
        "https://www.youtube.com/watch?v=EH7pUs6oPYk",
        "https://www.youtube.com/watch?v=XEVlyP4_11M",
        "https://www.youtube.com/watch?v=sBmVy85kPv4",
        "https://www.youtube.com/watch?v=HEew7ZqDjPk",
        "https://www.youtube.com/watch?v=AkY2hYEnv_0",
    ],
    "audiobook": [
        "https://www.youtube.com/watch?v=ZSi0E3M38AQ",
        "https://www.youtube.com/watch?v=7DtobAz19cg",
        "https://www.youtube.com/watch?v=MgYy8RHxUTc",
        "https://www.youtube.com/watch?v=w8HdOHrc3OQ",
        "https://www.youtube.com/watch?v=1BIeastO52I",
        "https://www.youtube.com/watch?v=rVOjw6nXJPQ",
        "https://www.youtube.com/watch?v=2LJ3mbJiAGQ",
        "https://www.youtube.com/watch?v=hS_AXRRnIzM",
        "https://www.youtube.com/watch?v=WjeOYl_sEjE",
        "https://www.youtube.com/watch?v=w7x_lWJNnNg",
    ],
    "meditation": [
        "https://www.youtube.com/watch?v=inpok4MKVLM",
        "https://www.youtube.com/watch?v=1ZYbU82GVz4",
        "https://www.youtube.com/watch?v=oCAFFIVxFO8",
        "https://www.youtube.com/watch?v=lFcSrYw-ARY",
        "https://www.youtube.com/watch?v=p5lL00dLvvQ",
        "https://www.youtube.com/watch?v=86r2Yx7eXmQ",
        "https://www.youtube.com/watch?v=t_c0YnJ_uMo",
        "https://www.youtube.com/watch?v=a2Gil8esNsI",
        "https://www.youtube.com/watch?v=6p6PcFFUARs",
        "https://www.youtube.com/watch?v=HdzI-191xhU",
    ],
    "conversation": [
        "https://www.youtube.com/watch?v=PMotykw0SIk",
        "https://www.youtube.com/watch?v=ycPr5-27vSI",
        "https://www.youtube.com/watch?v=BpBnJq19R60",
        "https://www.youtube.com/watch?v=6YLTLRxK5m8",
        "https://www.youtube.com/watch?v=1YbcB6b4A2U",
        "https://www.youtube.com/watch?v=aJX4ytfqw6k",
        "https://www.youtube.com/watch?v=MA4jJNlMiPo",
        "https://www.youtube.com/watch?v=MdZAMSyn_As",
        "https://www.youtube.com/watch?v=4kDyBqhXHLY",
        "https://www.youtube.com/watch?v=lI9Ri92N3wA",
    ]
}

def check_dependencies():
    """Check if required tools are installed"""
    missing = []
    
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, check=True)
    except:
        missing.append("yt-dlp")
    
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
    except:
        missing.append("ffmpeg")
    
    return missing

def create_directories():
    """Create necessary directories"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    Path(ZIP_DIR).mkdir(parents=True, exist_ok=True)

def download_audio(video_url, output_path):
    """Download audio from YouTube video"""
    try:
        if os.path.exists(output_path):
            return True
            
        cmd = [
            'yt-dlp',
            '-x',
            '--audio-format', 'wav',
            '--audio-quality', '0',
            '-o', output_path,
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            video_url
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return True
    except:
        return False

def split_audio_to_segments(input_file, category, base_name, duration=10):
    """Split audio file into segments"""
    segments = []
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(input_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        total_duration = float(result.stdout.strip())
    except:
        total_duration = 60
    
    num_segments = min(int(total_duration / duration), 10)
    
    for i in range(num_segments):
        start_time = i * duration
        output_name = f"{category}_{base_name}_seg{i+1:03d}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        if os.path.exists(output_path):
            segments.append(output_path)
            continue
        
        cmd = [
            'ffmpeg',
            '-i', str(input_file),
            '-ss', str(start_time),
            '-t', str(duration),
            '-ar', str(SAMPLE_RATE),
            '-ac', '1',
            '-sample_fmt', 's16',
            '-y',
            '-loglevel', 'error',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            segments.append(output_path)
        except:
            pass
    
    return segments

def convert_wav_to_mp3(wav_dir, mp3_dir):
    """Convert WAV files to MP3 format"""
    Path(mp3_dir).mkdir(parents=True, exist_ok=True)
    wav_files = list(Path(wav_dir).glob("*.wav"))
    converted = 0
    
    for wav_file in wav_files:
        mp3_file = Path(mp3_dir) / (wav_file.stem + ".mp3")
        
        if mp3_file.exists():
            converted += 1
            continue
        
        cmd = [
            'ffmpeg',
            '-i', str(wav_file),
            '-codec:a', 'libmp3lame',
            '-b:a', '128k',
            '-y',
            '-loglevel', 'error',
            str(mp3_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            converted += 1
        except:
            pass
    
    return converted

def create_zip_archive(source_dir, zip_path, file_pattern="*.mp3"):
    """Create a zip archive of files"""
    files = list(Path(source_dir).glob(file_pattern))
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file, file.name)
    
    return len(files)

def scrape_worker(category, videos, progress_queue, log_queue):
    """Worker function for scraping in background"""
    try:
        log_queue.put(f"Starting {category}...")
        downloaded = 0
        segments_created = 0
        
        for idx, video_url in enumerate(videos, 1):
            log_queue.put(f"[{category}] Downloading video {idx}/{len(videos)}...")
            
            temp_file = os.path.join(TEMP_DIR, f"{category}_temp_{idx}.wav")
            
            if download_audio(video_url, temp_file):
                if os.path.exists(temp_file):
                    base_name = f"vid{idx:03d}"
                    segments = split_audio_to_segments(temp_file, category, base_name, DURATION)
                    segments_created += len(segments)
                    
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                    
                    downloaded += 1
                    log_queue.put(f"[{category}] ✅ Video {idx}: {len(segments)} segments")
            
            progress_queue.put((category, idx, len(videos), segments_created))
            time.sleep(1)
        
        log_queue.put(f"✅ {category} complete: {segments_created} segments")
        return segments_created
    except Exception as e:
        log_queue.put(f"❌ Error in {category}: {str(e)}")
        return 0

# Streamlit UI
st.set_page_config(page_title="YouTube Safe Audio Scraper", page_icon="🎵", layout="wide")

st.title("🎵 YouTube Safe Audio Scraper")
st.markdown("Download safe audio from YouTube, convert to MP3, and create a zip archive")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")
target_files = st.sidebar.number_input("Target Files", min_value=100, max_value=1000, value=800, step=100)
segment_duration = st.sidebar.slider("Segment Duration (seconds)", 5, 20, 10)
videos_per_cat = st.sidebar.slider("Videos per Category", 5, 15, 10)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Output:** `{OUTPUT_DIR}`")
st.sidebar.markdown(f"**Sample Rate:** {SAMPLE_RATE}Hz")
st.sidebar.markdown(f"**Format:** WAV → MP3")

# Check dependencies
st.header("🔍 System Check")
missing = check_dependencies()

col1, col2 = st.columns(2)
with col1:
    if "yt-dlp" in missing:
        st.error("❌ yt-dlp not installed")
        st.code("pip install yt-dlp")
    else:
        st.success("✅ yt-dlp installed")

with col2:
    if "ffmpeg" in missing:
        st.error("❌ ffmpeg not installed")
        st.markdown("[Download ffmpeg](https://ffmpeg.org/download.html)")
    else:
        st.success("✅ ffmpeg installed")

# Check existing files
st.header("📊 Current Status")
create_directories()

existing_files = list(Path(OUTPUT_DIR).glob("*.wav"))
existing_count = len(existing_files)

col1, col2, col3 = st.columns(3)
col1.metric("WAV Files", existing_count)
col2.metric("Target", target_files)
col3.metric("Remaining", max(0, target_files - existing_count))

# Category breakdown
st.subheader("📁 Category Breakdown")
category_stats = {}
for cat_key, cat_name in CATEGORIES.items():
    count = len([f for f in existing_files if f.name.startswith(cat_key + "_")])
    category_stats[cat_name] = count

cols = st.columns(4)
for idx, (cat_name, count) in enumerate(category_stats.items()):
    with cols[idx % 4]:
        st.metric(cat_name, count)

# Main action buttons
st.header("🚀 Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Download Videos", type="primary", disabled=len(missing) > 0):
        if 'scraping_active' not in st.session_state:
            st.session_state.scraping_active = True
            st.session_state.progress_data = {}
            st.session_state.logs = []
            
            progress_bar = st.progress(0)
            log_container = st.container()
            
            progress_queue = queue.Queue()
            log_queue = queue.Queue()
            
            total_videos = len(CATEGORIES) * videos_per_cat
            completed_videos = 0
            
            threads = []
            for cat_key, cat_name in CATEGORIES.items():
                videos = SAFE_VIDEOS[cat_key][:videos_per_cat]
                thread = threading.Thread(
                    target=scrape_worker,
                    args=(cat_key, videos, progress_queue, log_queue)
                )
                thread.start()
                threads.append(thread)
            
            status_text = st.empty()
            
            while any(t.is_alive() for t in threads):
                while not log_queue.empty():
                    log = log_queue.get()
                    with log_container:
                        st.text(log)
                
                while not progress_queue.empty():
                    cat, vid_num, total_vids, segs = progress_queue.get()
                    completed_videos += 1
                    progress = completed_videos / total_videos
                    progress_bar.progress(progress)
                    status_text.text(f"Progress: {completed_videos}/{total_videos} videos")
                
                time.sleep(0.5)
            
            for thread in threads:
                thread.join()
            
            progress_bar.progress(1.0)
            st.success("✅ Download complete!")
            st.session_state.scraping_active = False
            st.rerun()

with col2:
    if st.button("🔄 Convert to MP3", disabled=existing_count == 0):
        with st.spinner("Converting WAV to MP3..."):
            mp3_dir = os.path.join(OUTPUT_DIR, "mp3")
            converted = convert_wav_to_mp3(OUTPUT_DIR, mp3_dir)
            st.success(f"✅ Converted {converted} files to MP3")
            st.session_state.mp3_ready = True

with col3:
    if st.button("📦 Create ZIP", disabled=existing_count == 0):
        with st.spinner("Creating ZIP archive..."):
            # First convert to MP3
            mp3_dir = os.path.join(OUTPUT_DIR, "mp3")
            convert_wav_to_mp3(OUTPUT_DIR, mp3_dir)
            
            # Create zip
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"safe_audio_{timestamp}.zip"
            zip_path = os.path.join(ZIP_DIR, zip_filename)
            
            file_count = create_zip_archive(mp3_dir, zip_path)
            
            st.success(f"✅ Created ZIP with {file_count} MP3 files")
            st.info(f"📦 File: `{zip_filename}`")
            
            # Provide download button
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=f,
                    file_name=zip_filename,
                    mime="application/zip"
                )

# Dataset info
st.header("ℹ️ About")
st.markdown("""
This tool downloads safe audio from YouTube across 8 categories:
- 🎙️ Podcast interviews
- 📚 Educational content
- 🎵 Instrumental music
- 📰 News broadcasts
- 💬 Conversations
- 🌿 Nature sounds
- 📖 Audiobooks
- 🧘 Meditation

**Process:**
1. Downloads videos from YouTube using yt-dlp
2. Splits into 10-second WAV segments (16kHz, mono)
3. Converts to MP3 for smaller file size
4. Creates a ZIP archive for easy download

**Requirements:**
- `yt-dlp` for downloading
- `ffmpeg` for audio processing
""")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Safe Audio Dataset Creator")
