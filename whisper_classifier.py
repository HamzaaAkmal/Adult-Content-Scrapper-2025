"""NSFW audio classification using Groq Whisper API."""

import asyncio
import aiohttp
import logging
import re
from typing import List, Dict, Optional
from config import (
    GROQ_API_KEY, GROQ_API_URL, WHISPER_MODEL,
    NSFW_KEYWORDS, NSFW_CATEGORIES, MIN_CONFIDENCE,
    MIN_KEYWORD_MATCHES, MIN_SEGMENT_LENGTH
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperClassifier:
    """Classifies audio using Groq Whisper API for NSFW content detection."""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.api_url = GROQ_API_URL
        self.model = WHISPER_MODEL
        
    async def transcribe_audio(self, audio_path: str) -> Optional[Dict]:
        """
        Transcribe audio file using Groq Whisper API.
        Returns verbose JSON with timestamps.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = aiohttp.FormData()
            data.add_field('model', self.model)
            data.add_field('temperature', '0')
            data.add_field('response_format', 'verbose_json')
            
            with open(audio_path, 'rb') as f:
                data.add_field('file', f, filename='audio.mp3')
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        data=data,
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Transcription successful for {audio_path}")
                            return result
                        else:
                            error_text = await response.text()
                            logger.error(f"API error {response.status}: {error_text}")
                            return None
                            
        except Exception as e:
            logger.error(f"Transcription error for {audio_path}: {e}")
            return None
    
    def classify_nsfw(self, transcription: Dict) -> List[Dict]:
        """
        Analyze transcription for NSFW content and return classified segments.
        Returns list of NSFW segments with timestamps, categories, and confidence.
        """
        if not transcription or 'segments' not in transcription:
            return []
        
        nsfw_segments = []
        text_full = transcription.get('text', '').lower()
        
        for segment in transcription.get('segments', []):
            segment_text = segment.get('text', '').lower()
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            
            # Analyze segment for NSFW content
            categories, confidence = self._analyze_segment(segment_text)
            
            if categories and confidence >= MIN_CONFIDENCE:
                nsfw_segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': segment_text,
                    'categories': categories,
                    'confidence': confidence
                })
        
        # Also check full text for patterns
        full_categories, full_confidence = self._analyze_segment(text_full)
        if full_categories and full_confidence >= MIN_CONFIDENCE and not nsfw_segments:
            # If no segments but full text is NSFW, create a general segment
            nsfw_segments.append({
                'start': 0,
                'end': transcription.get('duration', 10),
                'text': text_full[:100],
                'categories': full_categories,
                'confidence': full_confidence
            })
        
        logger.info(f"Found {len(nsfw_segments)} NSFW segments")
        return nsfw_segments
    
    def _analyze_segment(self, text: str) -> tuple:
        """
        Analyze text segment for NSFW categories with medium ML training criteria.
        Returns (categories list, confidence score).
        Enforces MIN_KEYWORD_MATCHES=1 and MIN_SEGMENT_LENGTH=2 for balanced quality.
        """
        # Filter by minimum segment length (word count)
        if len(text.split()) < MIN_SEGMENT_LENGTH:
            return [], 0.0
        
        detected_categories = []
        category_scores = {}
        total_keyword_matches = 0
        
        # Check for explicit keywords with medium matching
        for category, keywords in NSFW_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                total_keyword_matches += matches
                # Medium scoring for balanced training data
                if matches == 1:
                    score = 0.82  # Single match = 82%
                elif matches == 2:
                    score = 0.90  # Two matches = 90%
                else:
                    score = 0.95  # 3+ matches = 95%
                category_scores[category] = score
                detected_categories.append(category)
        
        # Enforce minimum keyword matches for quality
        if total_keyword_matches < MIN_KEYWORD_MATCHES:
            return [], 0.0
        
        # Phonetic/sound patterns (medium thresholds)
        vocal_pattern_strength = self._has_vocal_patterns(text)
        if vocal_pattern_strength >= 1:  # Need at least one pattern
            if 'moaning' not in category_scores:
                category_scores['moaning'] = 0.85
                detected_categories.append('moaning')
        
        breathing_pattern_strength = self._has_breathing_patterns(text)
        if breathing_pattern_strength >= 1:  # Need at least one pattern
            if 'heavy_breathing' not in category_scores:
                category_scores['heavy_breathing'] = 0.82
                detected_categories.append('heavy_breathing')
        
        # Calculate overall confidence (must meet MIN_CONFIDENCE=0.85)
        if category_scores:
            confidence = max(category_scores.values())
        else:
            confidence = 0.0
        
        return detected_categories, confidence
    
    def _has_vocal_patterns(self, text: str) -> int:
        """Detect moaning/vocal patterns in transcription. Returns pattern count for strict filtering."""
        patterns = [
            r'\b(ah+|oh+|uh+|mm+|ng+h)\b',
            r'[aeiou]{3,}',  # Extended vowel sounds
            r'\b(yeah|yes)\s+(yeah|yes)\b',  # Repetitive affirmations
            r'\b(ooh+|aah+)\b',  # Extended expressions
            r'\b(god|fuck|yes)\s+(god|fuck|yes)\b',  # Intense repetitions
        ]
        return sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
    
    def _has_breathing_patterns(self, text: str) -> int:
        """Detect heavy breathing patterns. Returns pattern count for strict filtering."""
        patterns = [
            r'\b(hah|huh|hff|pff)\b',
            r'\*\s*(breath|pant|gasp)',  # Action descriptions
            r'\b(harder|faster|deeper)\b',  # Intensity indicators
            r'\b(panting|gasping|moaning)\b',  # Explicit breathing descriptions
        ]
        return sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
    
    async def process_audio_file(self, audio_path: str) -> List[Dict]:
        """
        Full pipeline: transcribe and classify audio file.
        Returns list of NSFW segments.
        """
        transcription = await self.transcribe_audio(audio_path)
        if not transcription:
            return []
        
        return self.classify_nsfw(transcription)


async def classify_multiple_audios(audio_paths: List[str]) -> Dict[str, List[Dict]]:
    """Classify multiple audio files concurrently."""
    classifier = WhisperClassifier()
    
    tasks = [classifier.process_audio_file(path) for path in audio_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    classified = {}
    for path, result in zip(audio_paths, results):
        if isinstance(result, Exception):
            logger.error(f"Classification failed for {path}: {result}")
            classified[path] = []
        else:
            classified[path] = result
            
    return classified
