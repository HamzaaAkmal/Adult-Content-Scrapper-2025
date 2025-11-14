"""Video downloader using custom extractor and yt-dlp fallback."""

import asyncio
import aiohttp
import os
import subprocess
import logging
from typing import Optional, List
from pathlib import Path
from config import TEMP_DIR, MIN_VIDEO_DURATION, USER_AGENT
from custom_downloader import CustomVideoDownloader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDownloader:
    """Downloads videos from URLs using custom extractor or yt-dlp fallback."""
    
    def __init__(self):
        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(exist_ok=True)
        self.custom_downloader = CustomVideoDownloader()
        
    async def download_video(self, url: str, video_id: str) -> Optional[str]:
        """
        Download video from URL.
        Returns path to downloaded video file or None if failed.
        """
        logger.info(f"Downloading video from {url}")
        
        # Try custom downloader first (best for video pages)
        video_path = await self._download_with_custom(url, video_id)
        
        # Fallback to yt-dlp
        if not video_path:
            video_path = await self._download_with_ytdlp(url, video_id)
        
        # Last resort: direct download for direct video URLs
        if not video_path:
            video_path = await self._direct_download(url, video_id)
            
        if video_path and await self._validate_video(video_path):
            logger.info(f"Successfully downloaded: {video_path}")
            return video_path
        
        logger.warning(f"Failed to download or validate video from {url}")
        return None
    
    async def _download_with_custom(self, url: str, video_id: str) -> Optional[str]:
        """Download using custom page parser."""
        try:
            # Check if this is a video page URL (not a direct video file)
            if any(pattern in url.lower() for pattern in ['/video', '/watch', '/embed', '/play']):
                return await self.custom_downloader.download_from_page(url, video_id)
            return None
        except Exception as e:
            logger.error(f"Custom downloader error for {url}: {e}")
            return None
    
    async def _download_with_ytdlp(self, url: str, video_id: str) -> Optional[str]:
        """Download using yt-dlp."""
        output_path = self.temp_dir / f"{video_id}.%(ext)s"
        
        try:
            cmd = [
                "yt-dlp",
                url,
                "-f", "best[ext=mp4]/best",
                "-o", str(output_path),
                "--no-playlist",
                "--no-warnings",
                "--quiet",
                "--max-filesize", "500M",
                "--socket-timeout", "30"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.wait(), timeout=300)
            
            # Find downloaded file
            for file in self.temp_dir.glob(f"{video_id}.*"):
                if file.suffix in ['.mp4', '.webm', '.mkv', '.avi']:
                    return str(file)
                    
        except asyncio.TimeoutError:
            logger.error(f"yt-dlp timeout for {url}")
        except FileNotFoundError:
            logger.warning("yt-dlp not found, skipping")
        except Exception as e:
            logger.error(f"yt-dlp error for {url}: {e}")
            
        return None
    
    async def _direct_download(self, url: str, video_id: str) -> Optional[str]:
        """Direct download for MP4/video URLs."""
        if not any(ext in url.lower() for ext in ['.mp4', '.webm', '.avi', '.mov', '.mkv']):
            return None
            
        try:
            ext = url.split('.')[-1].split('?')[0]
            output_path = self.temp_dir / f"{video_id}.{ext}"
            
            headers = {"User-Agent": USER_AGENT}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=60) as response:
                    if response.status != 200:
                        return None
                        
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 500_000_000:  # 500MB
                        logger.warning(f"File too large: {url}")
                        return None
                    
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Direct download error for {url}: {e}")
            return None
    
    async def _validate_video(self, video_path: str) -> bool:
        """Validate video file and check duration."""
        try:
            # Get video duration using ffprobe
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            duration = float(stdout.decode().strip())
            
            if duration >= MIN_VIDEO_DURATION:
                return True
            else:
                logger.warning(f"Video too short: {duration}s")
                return False
                
        except Exception as e:
            logger.error(f"Video validation error: {e}")
            return False
    
    def cleanup(self, video_path: str):
        """Remove temporary video file."""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up: {video_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def download_videos_batch(urls: List[str], max_concurrent: int = 10) -> List[tuple]:
    """Download multiple videos concurrently."""
    downloader = VideoDownloader()
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_with_semaphore(url: str, idx: int):
        async with semaphore:
            video_id = f"video_{idx}_{hash(url) % 100000}"
            path = await downloader.download_video(url, video_id)
            return (url, path)
    
    tasks = [download_with_semaphore(url, i) for i, url in enumerate(urls)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for result in results:
        if isinstance(result, tuple) and result[1]:
            valid_results.append(result)
            
    return valid_results
