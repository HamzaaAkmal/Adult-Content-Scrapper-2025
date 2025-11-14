"""Custom video downloader for sites that yt-dlp struggles with."""

import asyncio
import aiohttp
import re
import logging
from typing import Optional
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import TEMP_DIR, USER_AGENT, MIN_VIDEO_DURATION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomVideoDownloader:
    """Custom downloader that extracts video URLs from HTML pages."""
    
    def __init__(self):
        self.temp_dir = Path(TEMP_DIR)
        self.temp_dir.mkdir(exist_ok=True)
        
    async def download_from_page(self, page_url: str, video_id: str) -> Optional[str]:
        """
        Extract video URL from a video page and download it.
        Works for sites like xhamster/hamsterix.
        
        Strategy:
        1. Try yt-dlp on the page URL first (most reliable)
        2. If that fails, extract video URL from HTML and download
        """
        try:
            logger.info(f"Downloading from page: {page_url}")
            
            # Try yt-dlp on the page URL first
            logger.info("Strategy 1: Trying yt-dlp on page URL")
            output_path = self.temp_dir / f"{video_id}.mp4"
            result = await self._download_with_ytdlp(page_url, str(output_path), page_url)
            if result:
                return result
            
            # Fallback: Extract video URL from page HTML
            logger.info("Strategy 2: Extracting video URL from HTML")
            video_url = await self._extract_video_url_from_page(page_url)
            
            if not video_url:
                logger.warning(f"Could not extract video URL from {page_url}")
                return None
            
            logger.info(f"Found video URL: {video_url[:100]}")
            
            # Download the video file
            output_path = await self._download_video_file(video_url, video_id, page_url)
            
            if output_path and await self._validate_video(output_path):
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"Custom download error for {page_url}: {e}")
            return None
    
    async def _extract_video_url_from_page(self, page_url: str) -> Optional[str]:
        """Extract the actual video file URL from a video page."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": page_url,
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(page_url, headers=headers, timeout=20, ssl=False) as response:
                    if response.status != 200:
                        logger.warning(f"Page returned status {response.status}")
                        return None
                    
                    html = await response.text()
                    
                    # Try multiple extraction methods
                    video_url = (
                        self._extract_from_json_ld(html) or
                        self._extract_from_player_config(html) or
                        self._extract_from_video_tags(html, page_url) or
                        self._extract_from_patterns(html)
                    )
                    
                    return video_url
                    
            except Exception as e:
                logger.error(f"Error fetching page {page_url}: {e}")
                return None
    
    def _extract_from_json_ld(self, html: str) -> Optional[str]:
        """Extract video URL from JSON-LD metadata."""
        try:
            # Look for JSON-LD script tags
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                if script.string and 'contentUrl' in script.string:
                    import json
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    
                    # Look for video URL
                    if 'contentUrl' in data:
                        return data['contentUrl']
                    if 'embedUrl' in data:
                        return data['embedUrl']
                        
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
        
        return None
    
    def _extract_from_player_config(self, html: str) -> Optional[str]:
        """Extract video URL from player configuration JavaScript."""
        # Common patterns in video player configs - prioritize direct MP4 URLs
        patterns = [
            # Direct MP4 URLs (highest priority)
            r'(https?://video\d+\.cdnsolutions\.media/[^"\s]+?/\d+/\d+/\d+/(?:720|1080|480)p\.h264\.mp4)',
            r'(https?://video\d+\.cdnsolutions\.media/[^"\s]+?\.mp4)',
            
            # XHamster/Hamsterix JSON patterns
            r'"(?:videoUrl|url|file)"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            r"'(?:videoUrl|url|file)'\s*:\s*'(https?://[^']+\.mp4[^']*)'",
            r'videoUrl\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            r'file\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            
            # Quality-specific patterns
            r'"1080p"\s*:\s*"(https?://[^"]+)"',
            r'"720p"\s*:\s*"(https?://[^"]+)"',
            r'"480p"\s*:\s*"(https?://[^"]+)"',
            r'"mp4"\s*:\s*"(https?://[^"]+)"',
            
            # Generic video URL patterns
            r'"sources"\s*:\s*\[?\s*{\s*"file"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            
            # CDN patterns (may include HLS as fallback)
            r'(https?://[^"\s]+cdnsolutions\.media[^"\s]+\.mp4)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                url = matches[0] if isinstance(matches[0], str) else matches[0]
                # Filter out thumbnails and previews
                if not any(x in url for x in ['/thumb-', '.t.mp4', '526x298', 'preview', 't.av1']):
                    # Prefer actual MP4 files over HLS
                    if '.mp4' in url and '.m3u8' not in url:
                        logger.debug(f"Found direct MP4 via pattern: {pattern[:50]}")
                        return url
        
        # If no direct MP4 found, try HLS as fallback
        hls_patterns = [
            r'"(?:url|file)"\s*:\s*"(https?://[^"]+\.m3u8[^"]*)"',
            r'(https?://video-nss\.cdnsolutions\.media/[^"\s]+?)',
        ]
        
        for pattern in hls_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                url = matches[0] if isinstance(matches[0], str) else matches[0]
                logger.debug(f"Found HLS stream: {url[:80]}")
                return url
        
        return None
    
    def _extract_from_video_tags(self, html: str, base_url: str) -> Optional[str]:
        """Extract from HTML5 video tags."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check video and source tags
            for tag in soup.find_all(['video', 'source']):
                for attr in ['src', 'data-src', 'data-video-url']:
                    src = tag.get(attr)
                    if src and '.mp4' in src:
                        # Make absolute URL
                        if not src.startswith('http'):
                            src = urljoin(base_url, src)
                        # Filter thumbnails
                        if not any(x in src for x in ['/thumb-', 't.mp4', '526x298']):
                            return src
                            
        except Exception as e:
            logger.debug(f"Video tag extraction failed: {e}")
        
        return None
    
    def _extract_from_patterns(self, html: str) -> Optional[str]:
        """Extract using aggressive pattern matching."""
        # Find all URLs that look like videos
        video_patterns = [
            r'(https?://video\d+\.cdnsolutions\.media/[^"\s]+?\.mp4)',
            r'(https?://[^"\s]+?cdnsolutions\.media/[^"\s]+?/\d+/\d+/\d+/\d+p\.h264\.mp4)',
            r'(https?://[^"\s]+?xhcdn\.com/[^"\s]+?\.mp4)',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                # Filter out thumbnails and previews
                if not any(x in match for x in ['/thumb-', '.t.mp4', '526x298', 'preview', '.webm']):
                    # Prefer higher quality
                    if any(q in match for q in ['720p', '1080p', '480p']):
                        return match
        
        # Return any video URL as fallback
        for pattern in video_patterns:
            matches = re.findall(pattern, html)
            if matches:
                return matches[0]
        
        return None
    
    async def _download_video_file(self, video_url: str, video_id: str, referer: str) -> Optional[str]:
        """Download the actual video file - tries multiple methods for maximum compatibility."""
        try:
            output_path = self.temp_dir / f"{video_id}.mp4"
            
            # Try ffmpeg first - it's most reliable for various CDN formats
            logger.info(f"Attempting download with ffmpeg: {video_url[:80]}")
            result = await self._download_with_ffmpeg(video_url, str(output_path), referer)
            if result:
                return result
            
            # If ffmpeg fails and it's not an HLS stream, try direct HTTP
            if '.m3u8' not in video_url and 'hls' not in video_url.lower():
                logger.info(f"ffmpeg failed, trying HTTP download: {video_url[:80]}")
                result = await self._download_http(video_url, str(output_path), referer)
                if result:
                    return result
            
            # Last resort: try yt-dlp
            logger.info(f"Trying yt-dlp as fallback: {video_url[:80]}")
            result = await self._download_with_ytdlp(video_url, str(output_path), referer)
            return result
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def _download_with_ffmpeg(self, video_url: str, output_path: str, referer: str) -> Optional[str]:
        """Download HLS or other streams using ffmpeg."""
        try:
            cmd = [
                'ffmpeg',
                '-headers', f'Referer: {referer}',
                '-user_agent', USER_AGENT,
                '-i', video_url,
                '-c', 'copy',  # Copy codec without re-encoding (faster)
                '-bsf:a', 'aac_adtstoasc',  # Fix AAC issues
                '-y',  # Overwrite
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for download with timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=300)  # 5 min timeout
                
                if process.returncode == 0 and Path(output_path).exists():
                    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
                    logger.info(f"ffmpeg download complete: {size_mb:.2f} MB")
                    return output_path
                else:
                    logger.warning(f"ffmpeg failed with return code {process.returncode}")
                    return None
                    
            except asyncio.TimeoutError:
                process.kill()
                logger.error("ffmpeg download timeout")
                return None
                
        except Exception as e:
            logger.error(f"ffmpeg download error: {e}")
            return None
    
    async def _download_http(self, video_url: str, output_path: str, referer: str) -> Optional[str]:
        """Download regular video file via HTTP with retry logic."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': USER_AGENT,
                    'Referer': referer,
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'identity',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'video',
                    'Sec-Fetch-Mode': 'no-cors',
                }
                
                logger.info(f"Downloading regular MP4 (attempt {attempt+1}/{max_retries}): {video_url[:80]}")
                
                timeout = aiohttp.ClientTimeout(total=600, connect=30)  # 10min total, 30s connect
                connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification if needed
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(video_url, headers=headers) as response:
                        if response.status not in [200, 206]:
                            logger.warning(f"HTTP {response.status} for {video_url[:80]}, retrying...")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            return None
                        
                        # Check file size
                        content_length = response.headers.get('content-length')
                        if content_length:
                            size_mb = int(content_length) / (1024 * 1024)
                            logger.info(f"Downloading {size_mb:.2f} MB")
                            
                            if size_mb > 500:
                                logger.warning("File too large (>500MB)")
                                return None
                        
                        # Download in chunks
                        downloaded = 0
                        with open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                        
                        logger.info(f"Downloaded {downloaded / (1024*1024):.2f} MB to {output_path}")
                        
                        # Validate the downloaded file
                        if Path(output_path).exists() and Path(output_path).stat().st_size > 1024:
                            if await self._validate_video(output_path):
                                return output_path
                            else:
                                logger.warning(f"Validation failed for {output_path}, retrying...")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay * (attempt + 1))
                                    continue
                                return None
                        else:
                            logger.warning(f"Downloaded file too small or missing, retrying...")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            return None
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading {video_url[:80]}, attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All retry attempts failed due to timeout")
                    return None
            except Exception as e:
                logger.error(f"HTTP download error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    return None
        
        return None
    
    async def _download_with_ytdlp(self, video_url: str, output_path: str, referer: str) -> Optional[str]:
        """Download using yt-dlp as last resort fallback."""
        try:
            cmd = [
                'yt-dlp',
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                '--add-header', f'Referer:{referer}',
                '--user-agent', USER_AGENT,
                '-o', output_path,
                '-f', 'best[ext=mp4]/best',
                video_url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                
                if process.returncode == 0 and Path(output_path).exists():
                    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
                    logger.info(f"yt-dlp download complete: {size_mb:.2f} MB")
                    return output_path
                else:
                    logger.warning(f"yt-dlp failed: {stderr.decode()[:200]}")
                    return None
                    
            except asyncio.TimeoutError:
                process.kill()
                logger.error("yt-dlp download timeout")
                return None
                
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None
    
    async def _validate_video(self, video_path: str) -> bool:
        """Validate video file using ffprobe."""
        try:
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
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.warning(f"ffprobe validation failed: {stderr.decode()}")
                return False
            
            duration = float(stdout.decode().strip())
            
            if duration >= MIN_VIDEO_DURATION:
                logger.info(f"Video validated: {duration:.1f}s")
                return True
            else:
                logger.warning(f"Video too short: {duration}s")
                return False
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def cleanup(self, video_path: str):
        """Remove temporary video file."""
        try:
            if video_path and Path(video_path).exists():
                Path(video_path).unlink()
                logger.info(f"Cleaned up: {video_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
