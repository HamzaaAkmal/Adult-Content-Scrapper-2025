"""Main orchestrator for the NSFW audio scraping pipeline."""

import asyncio
import logging
from typing import List, Dict
from pathlib import Path
import shutil
from datetime import datetime

from web_crawler import WebCrawler
from custom_downloader import CustomVideoDownloader  # Use custom downloader
from whisper_classifier import WhisperClassifier
from clip_extractor import ClipExtractor
from config import MAX_CONCURRENT_SCRAPES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NSFWScraper:
    """Main orchestrator for scraping NSFW audio clips."""
    
    def __init__(self, progress_callback=None):
        self.crawler = WebCrawler()
        self.downloader = CustomVideoDownloader()  # Use custom downloader
        self.classifier = WhisperClassifier()
        self.extractor = ClipExtractor()
        self.progress_callback = progress_callback
    
    def cleanup_old_data(self):
        """Clean up old temporary files and ZIPs before starting fresh scrape."""
        from config import TEMP_DIR, BASE_DIR
        
        logger.info("Cleaning up old temporary files and ZIPs...")
        
        # Clean temp directory
        temp_dir = Path(TEMP_DIR)
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Could not delete {item}: {e}")
        
        # Clean old ZIP files
        base_dir = Path(BASE_DIR)
        for old_zip in base_dir.glob("nsfw_clips_*.zip"):
            try:
                old_zip.unlink()
                logger.info(f"Deleted old ZIP: {old_zip.name}")
            except Exception as e:
                logger.warning(f"Could not delete {old_zip.name}: {e}")
        
        logger.info("Cleanup complete - ready for fresh data collection")
        
    async def scrape_from_urls(self, website_urls: List[str], clean_old_data: bool = True) -> Dict:
        """
        Main pipeline: crawl websites → download videos → classify → extract clips.
        
        Args:
            website_urls: List of URLs to scrape
            clean_old_data: If True, cleans temp files and old ZIPs before starting
        """
        # Clean old data if requested
        if clean_old_data:
            self.cleanup_old_data()
        
        results = {
            'total_websites': len(website_urls),
            'videos_found': 0,
            'videos_downloaded': 0,
            'clips_extracted': 0,
            'clips_metadata': [],
            'errors': []
        }
        
        # Step 1: Crawl websites to find video URLs
        self._update_progress("Crawling websites for video URLs...")
        video_urls_by_site = await self._crawl_websites(website_urls)
        
        all_video_urls = []
        for site, urls in video_urls_by_site.items():
            all_video_urls.extend([(url, site) for url in urls])
        
        results['videos_found'] = len(all_video_urls)
        logger.info(f"Found {len(all_video_urls)} video URLs across {len(website_urls)} websites")
        
        if not all_video_urls:
            return results
        
        # Step 2: Download and process videos
        self._update_progress(f"Processing {len(all_video_urls)} videos...")
        clips_metadata = await self._process_videos(all_video_urls, results)
        
        results['clips_metadata'] = clips_metadata
        results['clips_extracted'] = len(clips_metadata)
        
        # Step 3: Save master metadata
        if clips_metadata:
            self.extractor.save_master_metadata(clips_metadata)
            results['statistics'] = self.extractor.get_statistics(clips_metadata)
        
        logger.info(f"Scraping complete: {results['clips_extracted']} clips extracted")
        return results
    
    async def _crawl_websites(self, urls: List[str]) -> Dict[str, List[str]]:
        """Crawl multiple websites to find video URLs."""
        results = {}
        
        for url in urls:
            try:
                video_urls = await self.crawler.crawl_site(url)
                results[url] = video_urls
                self._update_progress(f"Found {len(video_urls)} videos from {url}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                results[url] = []
        
        return results
    
    async def _process_videos(self, video_urls: List[tuple], results: Dict) -> List[Dict]:
        """Download, classify, and extract clips from videos."""
        all_clips = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)
        
        async def process_single_video(video_url: str, source_site: str, index: int):
            async with semaphore:
                try:
                    self._update_progress(f"Processing video {index + 1}/{len(video_urls)}")
                    
                    # Download video using custom downloader (works with page URLs)
                    video_id = f"video_{index}_{hash(video_url) % 100000}"
                    video_path = await self.downloader.download_from_page(video_url, video_id)
                    
                    if not video_path:
                        return []
                    
                    results['videos_downloaded'] += 1
                    
                    # Extract audio for classification
                    audio_path = await self._extract_audio_temp(video_path, video_id)
                    
                    if not audio_path:
                        self.downloader.cleanup(video_path)
                        return []
                    
                    # Classify audio
                    nsfw_segments = await self.classifier.process_audio_file(audio_path)
                    
                    # Extract clips if NSFW content found
                    clips = []
                    if nsfw_segments:
                        clips = await self.extractor.extract_clips(
                            video_path,
                            nsfw_segments,
                            video_url
                        )
                    
                    # Cleanup
                    self.downloader.cleanup(video_path)
                    self.downloader.cleanup(audio_path)
                    
                    return clips
                    
                except Exception as e:
                    logger.error(f"Error processing video {video_url}: {e}")
                    results['errors'].append({'url': video_url, 'error': str(e)})
                    return []
        
        # Process all videos concurrently
        tasks = [
            process_single_video(url, site, idx)
            for idx, (url, site) in enumerate(video_urls)
        ]
        
        video_clips = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for clips in video_clips:
            if isinstance(clips, list):
                all_clips.extend(clips)
        
        return all_clips
    
    async def _extract_audio_temp(self, video_path: str, video_id: str) -> str:
        """Extract audio from video for Whisper processing."""
        try:
            from pathlib import Path
            temp_audio = Path(video_path).parent / f"{video_id}_audio.mp3"
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-b:a', '128k',
                '-ar', '16000',  # Whisper works well with 16kHz
                '-y',
                str(temp_audio)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.wait(), timeout=60)
            
            if process.returncode == 0:
                return str(temp_audio)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return None
    
    def _update_progress(self, message: str):
        """Update progress callback if provided."""
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def create_download_zip(self, output_zip: str = "nsfw_clips.zip") -> str:
        """Create a ZIP file of ONLY the latest clips and metadata. Cleans old ZIPs first."""
        try:
            from config import CLIPS_DIR, METADATA_DIR, BASE_DIR
            import zipfile
            import glob
            
            # Step 1: Delete all old ZIP files in the base directory
            logger.info("Cleaning up old ZIP files...")
            base_dir = Path(BASE_DIR)
            for old_zip in base_dir.glob("nsfw_clips_*.zip"):
                try:
                    old_zip.unlink()
                    logger.info(f"Deleted old ZIP: {old_zip.name}")
                except Exception as e:
                    logger.warning(f"Could not delete {old_zip.name}: {e}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_path = base_dir / f"nsfw_clips_{timestamp}.zip"
            
            # Step 2: Create fresh ZIP with ONLY current data
            logger.info("Creating fresh ZIP with latest data only...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add clips (organized by category)
                clips_dir = Path(CLIPS_DIR)
                if clips_dir.exists():
                    for category_dir in clips_dir.iterdir():
                        if category_dir.is_dir() and not category_dir.name.startswith('.'):
                            # Add all files in this category
                            for file_path in category_dir.rglob('*'):
                                if file_path.is_file():
                                    arcname = str(file_path.relative_to(clips_dir.parent))
                                    zipf.write(file_path, arcname)
                
                # Add metadata files
                metadata_dir = Path(METADATA_DIR)
                if metadata_dir.exists():
                    for meta_file in metadata_dir.glob('*.json'):
                        arcname = f"metadata/{meta_file.name}"
                        zipf.write(meta_file, arcname)
            
            logger.info(f"Created fresh ZIP archive: {zip_path} (old ZIPs removed)")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}")
            return None


# Convenience function for running the scraper
async def run_scraper(website_urls: List[str], progress_callback=None) -> Dict:
    """Run the complete scraping pipeline."""
    scraper = NSFWScraper(progress_callback)
    results = await scraper.scrape_from_urls(website_urls)
    return results
