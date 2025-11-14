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
        
    async def scrape_from_urls(self, website_urls: List[str]) -> Dict:
        """
        Main pipeline: crawl websites → download videos → classify → extract clips.
        """
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
        """Create a ZIP file of all extracted clips and metadata."""
        try:
            from config import CLIPS_DIR, METADATA_DIR
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_name = f"nsfw_clips_{timestamp}"
            
            # Create archive
            archive_path = shutil.make_archive(
                zip_name,
                'zip',
                root_dir=Path(CLIPS_DIR).parent,
                base_dir=Path(CLIPS_DIR).name
            )
            
            # Also add metadata
            if Path(METADATA_DIR).exists():
                import zipfile
                with zipfile.ZipFile(archive_path, 'a') as zipf:
                    for meta_file in Path(METADATA_DIR).glob('*.json'):
                        zipf.write(meta_file, f'metadata/{meta_file.name}')
            
            logger.info(f"Created ZIP archive: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}")
            return None


# Convenience function for running the scraper
async def run_scraper(website_urls: List[str], progress_callback=None) -> Dict:
    """Run the complete scraping pipeline."""
    scraper = NSFWScraper(progress_callback)
    results = await scraper.scrape_from_urls(website_urls)
    return results
