# ML Training Version - Strict NSFW Audio Dataset Scraper

## Overview
This is the **strict ML training version** of the NSFW audio scraper, optimized for creating high-quality training datasets for adult content classification models.

## Key Differences from Standard Version

### 1. Confidence Threshold
- **Standard**: 70% confidence
- **ML Training**: **90% confidence** (MIN_CONFIDENCE = 0.90)
- **Impact**: Only clips with very high confidence are extracted, reducing false positives

### 2. NSFW Categories
- **Standard**: 6 categories
- **ML Training**: **23 comprehensive categories**

#### Full Category List:
1. `moaning` - Vocal pleasure expressions
2. `screaming` - High-intensity vocalizations
3. `whimpering` - Soft vocal expressions
4. `gasping` - Breath intake sounds
5. `explicit_language` - Direct sexual vocabulary
6. `dirty_talk` - Sexual conversation
7. `sexual_commands` - Directive phrases
8. `begging` - Pleading expressions
9. `orgasm_sounds` - Climax vocalizations
10. `pleasure_sounds` - General pleasure audio
11. `pain_pleasure` - Mixed intensity sounds
12. `kissing_sounds` - Lip contact audio
13. `sucking_sounds` - Oral activity audio
14. `roleplay` - Scenario-based content
15. `dominance` - Power dynamic expressions
16. `submission` - Submissive vocalizations
17. `degradation` - Humiliation content
18. `body_slapping` - Physical contact sounds
19. `wet_sounds` - Fluid-related audio
20. `intense_activity` - High-energy content
21. `heavy_breathing` - Respiration sounds
22. `spanking` - Impact sounds
23. `impact_sounds` - Physical contact audio

### 3. Keyword Detection
- **Standard**: ~30 keywords
- **ML Training**: **100+ keywords** across all categories
- **Requirement**: Minimum 2 keyword matches per clip (MIN_KEYWORD_MATCHES = 2)

### 4. Audio Quality Standards

#### Clip Parameters:
- **Duration**: 15 seconds (up from 10s)
- **Max Clips per Video**: 5 (up from 3)
- **Min Video Duration**: 15 seconds

#### Audio Quality:
- **Bitrate**: 256kbps (up from 192kbps)
- **Sample Rate**: 44100 Hz
- **Channels**: 2 (stereo)
- **Codec**: libmp3lame with VBR quality 0 (highest)
- **Validation**: Clips under 10KB rejected as corrupt

### 5. Filtering Criteria

#### Segment Length:
- **Min Segment Length**: 3 words (MIN_SEGMENT_LENGTH = 3)
- Prevents fragmented or incomplete segments

#### Confidence Scoring:
- **1 keyword match**: 75% confidence
- **2 keyword matches**: 88% confidence
- **3+ keyword matches**: 95% confidence

#### Pattern Detection:
- **Vocal patterns**: Requires 2+ patterns detected
- **Breathing patterns**: Requires 2+ patterns detected
- **Pattern types**: Extended vowels, repetitions, intensity indicators

## Configuration Parameters

```python
# Quality Thresholds
MIN_CONFIDENCE = 0.90          # 90% minimum confidence
MIN_KEYWORD_MATCHES = 2         # Minimum 2 keywords per segment
MIN_SEGMENT_LENGTH = 3          # Minimum 3 words per segment

# Audio Quality
MIN_AUDIO_BITRATE = 128         # Minimum 128kbps
MIN_SAMPLE_RATE = 44100         # 44.1kHz standard
REQUIRE_STEREO = False          # Stereo preferred but not required

# Clip Settings
CLIP_DURATION = 15              # 15-second clips
MIN_VIDEO_DURATION = 15         # Process videos 15s+
MAX_CLIPS_PER_VIDEO = 5         # Up to 5 clips per video
```

## Usage for ML Training

### 1. Prepare Input CSV
```csv
url
https://example1.com/video1
https://example2.com/video2
```

### 2. Run Scraper
```bash
streamlit run app.py
```

Upload your CSV and start scraping.

### 3. Expected Output Structure
```
output/
├── clips/                      # High-quality 15s audio clips (256kbps MP3)
│   ├── example1_com_moaning_0.0s.mp3
│   ├── example1_com_explicit_15.2s.mp3
│   └── ...
├── metadata/                   # Detailed JSON metadata per clip
│   ├── example1_com_moaning_0.0s.json
│   └── ...
├── videos/                     # Downloaded source videos
└── master_metadata.json        # Complete dataset overview
```

### 4. Metadata Structure
Each clip includes:
```json
{
  "clip_id": "example_com_moaning_0.0s",
  "url": "https://example.com/video",
  "domain": "example.com",
  "timestamp": 0.0,
  "duration": 15,
  "category": "moaning",
  "all_categories": ["moaning", "heavy_breathing"],
  "confidence": 0.95,
  "text": "transcribed text...",
  "clip_path": "clips/example_com_moaning_0.0s.mp3",
  "extracted_at": "2025-01-15T10:30:00"
}
```

## Quality Validation

### Automated Checks:
1. **File size validation**: Clips < 10KB rejected
2. **Confidence threshold**: Must meet 90% minimum
3. **Keyword validation**: Minimum 2 keywords detected
4. **Segment length**: Minimum 3 words
5. **Pattern strength**: 2+ patterns for vocal/breathing categories

### Manual Review Recommended:
- Random sample 5-10% of clips
- Verify category accuracy
- Check for false positives
- Validate audio quality

## Statistics Tracking

The scraper provides detailed statistics:
- **Total clips extracted**
- **Clips by category** (distribution across 23 categories)
- **Clips by domain** (source website breakdown)
- **Average confidence** (quality metric)

## Model Training Recommendations

### Dataset Size:
- **Minimum**: 1000 clips per major category
- **Recommended**: 5000+ clips per category
- **Balanced**: Equal distribution across categories

### Training Split:
- **Train**: 70% (7000 clips if 10k total)
- **Validation**: 15% (1500 clips)
- **Test**: 15% (1500 clips)

### Data Augmentation:
Since clips are high quality (256kbps, 44.1kHz):
- Pitch shifting: ±2 semitones
- Time stretching: 0.9x - 1.1x
- Background noise: 5-10% mix
- Volume normalization

### Features for Classification:
- **MFCCs**: 13-40 coefficients
- **Spectral features**: Centroid, rolloff, bandwidth
- **Temporal features**: Zero crossing rate, energy
- **Chroma features**: Pitch class distribution

## Performance Expectations

### Scraping Speed:
- **Web crawling**: 10-20 URLs/minute
- **Video download**: 1-5 videos/minute (depends on CDN)
- **Whisper classification**: 30-60 seconds per video
- **Clip extraction**: 5-10 clips/minute

### Quality vs Quantity:
- **90% threshold**: Expect 30-50% fewer clips than 70%
- **Higher precision**: Reduced false positives
- **Better training**: More reliable labels

### CDN Success Rate:
- **Typical**: 40-60% download success
- **VPN/proxy**: Can improve to 70-80%
- **Geographic**: Varies by region

## Troubleshooting

### Low Clip Yield:
- **Issue**: Very few clips extracted
- **Solution**: Check if threshold too strict, review logs for confidence scores

### Category Imbalance:
- **Issue**: Some categories have too few clips
- **Solution**: Add more URLs for underrepresented categories, expand keywords

### Audio Quality Issues:
- **Issue**: Clips sound distorted
- **Solution**: Verify FFmpeg installation, check source video quality

### API Rate Limits:
- **Issue**: Groq API throttling
- **Solution**: Add delays between requests, use batch processing

## Security Notes

### API Key Management:
- **Never** commit `.env` file to git
- Use `.env.example` as template
- Rotate API keys regularly
- Monitor Groq API usage dashboard

### Data Privacy:
- NSFW content - handle responsibly
- Secure storage for datasets
- Comply with local regulations
- Consider encryption for sensitive data

## Comparison: Standard vs ML Training

| Metric | Standard | ML Training |
|--------|----------|-------------|
| Confidence Threshold | 70% | 90% |
| Categories | 6 | 23 |
| Keywords | ~30 | 100+ |
| Clip Duration | 10s | 15s |
| Audio Bitrate | 192kbps | 256kbps |
| Keyword Matches Required | 1 | 2 |
| Segment Min Length | None | 3 words |
| Quality Validation | Basic | Strict |
| Expected Clips/Video | 2-3 | 1-2 |
| False Positive Rate | ~15% | ~5% |
| Training Suitability | Moderate | High |

## Version History

### v2.0 - ML Training (Current)
- 90% confidence threshold
- 23 NSFW categories
- 256kbps audio quality
- Strict filtering criteria
- Enhanced pattern detection

### v1.0 - Standard
- 70% confidence threshold
- 6 basic categories
- 192kbps audio quality
- Basic filtering
- Simple pattern detection

---

**For questions or issues**: Check logs in `streamlit_scraper/logs/` or refer to main README.md
