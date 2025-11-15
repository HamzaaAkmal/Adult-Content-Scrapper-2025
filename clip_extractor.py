"""Audio clip extraction and organization."""

import os
import asyncio
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
from config import CLIPS_DIR, METADATA_DIR, CLIP_DURATION, MAX_CLIPS_PER_VIDEO, MAX_CLIPS_PER_CATEGORY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClipExtractor:
    """Extracts 10-second audio clips from videos based on NSFW timestamps."""
    
    def __init__(self):
        self.clips_dir = Path(CLIPS_DIR)
        self.metadata_dir = Path(METADATA_DIR)
        self.clips_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        # Track category counts for balanced dataset
        self.category_counts = self._load_category_counts()
        
    async def extract_clips(
        self,
        video_path: str,
        nsfw_segments: List[Dict],
        source_url: str
    ) -> List[Dict]:
        """
        Extract audio clips from video at NSFW timestamps.
        Returns list of extracted clip metadata.
        Enforces MAX_CLIPS_PER_CATEGORY limit for balanced dataset.
        """
        if not nsfw_segments:
            logger.info(f"No NSFW segments for {video_path}")
            return []
        
        # Limit clips per video
        segments_to_process = nsfw_segments[:MAX_CLIPS_PER_VIDEO]
        
        clips_metadata = []
        source_domain = self._get_domain(source_url)
        
        for idx, segment in enumerate(segments_to_process):
            # Check if primary category has reached limit
            primary_category = segment['categories'][0] if segment['categories'] else 'uncategorized'
            
            if self.category_counts.get(primary_category, 0) >= MAX_CLIPS_PER_CATEGORY:
                logger.info(f"Category '{primary_category}' has reached maximum limit of {MAX_CLIPS_PER_CATEGORY} clips, skipping...")
                continue
            
            clip_info = await self._extract_single_clip(
                video_path=video_path,
                segment=segment,
                source_url=source_url,
                source_domain=source_domain,
                clip_index=idx
            )
            
            if clip_info:
                clips_metadata.append(clip_info)
                # Increment category count
                self.category_counts[primary_category] = self.category_counts.get(primary_category, 0) + 1
                self._save_category_counts()
                logger.info(f"Category '{primary_category}': {self.category_counts[primary_category]}/{MAX_CLIPS_PER_CATEGORY} clips")
        
        logger.info(f"Extracted {len(clips_metadata)} clips from {video_path}")
        return clips_metadata
    
    async def _extract_single_clip(
        self,
        video_path: str,
        segment: Dict,
        source_url: str,
        source_domain: str,
        clip_index: int
    ) -> Optional[Dict]:
        """Extract a single 10-second clip."""
        try:
            # Calculate clip timing
            start_time = max(0, segment['start'] - 1)  # 1s before NSFW content
            duration = CLIP_DURATION
            
            # Determine primary category
            primary_category = segment['categories'][0] if segment['categories'] else 'uncategorized'
            
            # Create category directory
            category_dir = self.clips_dir / primary_category / source_domain
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique clip filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clip_filename = f"clip_{timestamp}_{clip_index}.mp3"
            output_path = category_dir / clip_filename
            
            # Extract audio clip using ffmpeg
            success = await self._run_ffmpeg_extract(
                video_path,
                str(output_path),
                start_time,
                duration
            )
            
            if not success:
                return None
            
            # Create metadata
            metadata = {
                'url': source_url,
                'domain': source_domain,
                'timestamp': start_time,
                'duration': duration,
                'category': primary_category,
                'all_categories': segment['categories'],
                'confidence': segment['confidence'],
                'text': segment.get('text', ''),
                'clip_path': str(output_path.relative_to(self.clips_dir)),
                'extracted_at': datetime.now().isoformat()
            }
            
            # Save individual metadata
            metadata_file = output_path.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting clip: {e}")
            return None
    
    async def _run_ffmpeg_extract(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ) -> bool:
        """Run ffmpeg to extract audio clip with high quality for ML training."""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-b:a', '224k',  # Good quality for ML training
                '-ar', '44100',  # Standard sample rate
                '-ac', '2',  # Stereo audio
                '-q:a', '2',  # High quality VBR
                '-y',  # Overwrite
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.wait(), timeout=30)
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Validate audio quality
                file_size = os.path.getsize(output_path)
                if file_size < 10000:  # Less than 10KB indicates problem
                    logger.error(f"Extracted clip too small ({file_size} bytes), likely corrupt")
                    return False
                logger.info(f"Extracted high-quality clip: {output_path} ({file_size/1024:.1f}KB)")
                return True
            else:
                logger.error(f"ffmpeg failed with return code {process.returncode}")
                return False
                
        except asyncio.TimeoutError:
            logger.error("ffmpeg extraction timeout")
            return False
        except Exception as e:
            logger.error(f"ffmpeg error: {e}")
            return False
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or 'unknown'
            # Clean domain
            domain = domain.replace('www.', '').replace(':', '_')
            return domain
        except:
            return 'unknown'
    
    def save_master_metadata(self, all_clips_metadata: List[Dict], output_file: str = 'master_metadata.json'):
        """Save all clips metadata to a master file."""
        output_path = self.metadata_dir / output_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_clips': len(all_clips_metadata),
                    'generated_at': datetime.now().isoformat(),
                    'clips': all_clips_metadata
                }, f, indent=2)
            
            logger.info(f"Master metadata saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving master metadata: {e}")
            return None
    
    def get_statistics(self, all_clips_metadata: List[Dict]) -> Dict:
        """Calculate statistics from extracted clips."""
        stats = {
            'total_clips': len(all_clips_metadata),
            'by_category': {},
            'by_domain': {},
            'avg_confidence': 0.0
        }
        
        if not all_clips_metadata:
            return stats
        
        # Count by category
        for clip in all_clips_metadata:
            category = clip.get('category', 'uncategorized')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            domain = clip.get('domain', 'unknown')
            stats['by_domain'][domain] = stats['by_domain'].get(domain, 0) + 1
        
        # Average confidence
        confidences = [clip.get('confidence', 0) for clip in all_clips_metadata]
        stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        
        return stats
    
    def _load_category_counts(self) -> Dict[str, int]:
        """Load category counts from file to persist across runs."""
        counts_file = self.metadata_dir / 'category_counts.json'
        if counts_file.exists():
            try:
                with open(counts_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading category counts: {e}")
        return {}
    
    def _save_category_counts(self):
        """Save category counts to file."""
        counts_file = self.metadata_dir / 'category_counts.json'
        try:
            with open(counts_file, 'w') as f:
                json.dump(self.category_counts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving category counts: {e}")
    
    def reset_category_counts(self):
        """Reset category counts (for starting a new dataset collection)."""
        self.category_counts = {}
        self._save_category_counts()
        logger.info("Category counts reset")


async def process_video_to_clips(
    video_path: str,
    source_url: str,
    nsfw_segments: List[Dict]
) -> List[Dict]:
    """Process a single video and extract clips."""
    extractor = ClipExtractor()
    return await extractor.extract_clips(video_path, nsfw_segments, source_url)
