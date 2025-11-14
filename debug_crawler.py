"""Debug script to test web crawler on specific URLs."""

import asyncio
import sys
import os
import logging

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_crawler import WebCrawler
from bs4 import BeautifulSoup
import aiohttp

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_crawler(url: str):
    """Test crawler on a specific URL with detailed output."""
    print("=" * 80)
    print(f"Testing crawler on: {url}")
    print("=" * 80)
    
    crawler = WebCrawler(max_depth=3, max_urls_per_site=100)
    
    # First, just fetch the page and examine it
    print("\n1. Fetching homepage...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=20, ssl=False) as response:
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"   HTML Length: {len(html)} chars")
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Check for common video indicators
                    print("\n2. Analyzing page structure...")
                    
                    video_tags = soup.find_all(['video', 'source'])
                    print(f"   <video>/<source> tags: {len(video_tags)}")
                    
                    iframes = soup.find_all('iframe')
                    print(f"   <iframe> tags: {len(iframes)}")
                    if iframes:
                        for i, iframe in enumerate(iframes[:3]):
                            print(f"      iframe {i+1}: {iframe.get('src', 'no src')[:80]}")
                    
                    all_links = soup.find_all('a', href=True)
                    print(f"   Total links: {len(all_links)}")
                    
                    # Check for video-like links
                    video_like_links = []
                    for link in all_links:
                        href = link.get('href', '').lower()
                        text = link.get_text().strip().lower()
                        
                        if any(term in href for term in ['/video', '/watch', '/play', '/embed', '/clip', '.mp4', '.webm']):
                            video_like_links.append((href, text))
                        elif any(term in text for term in ['video', 'watch', 'play', 'clip']):
                            video_like_links.append((href, text))
                    
                    print(f"   Video-like links found: {len(video_like_links)}")
                    if video_like_links:
                        print("\n   Sample video-like links:")
                        for href, text in video_like_links[:10]:
                            print(f"      {href[:60]} | Text: {text[:30]}")
                    
                    # Check meta tags
                    meta_video = soup.find_all('meta', attrs={'property': lambda x: x and 'video' in x.lower()})
                    print(f"\n   Meta video tags: {len(meta_video)}")
                    
                    # Check for data attributes
                    data_video = soup.find_all(attrs={'data-video': True}) + \
                                soup.find_all(attrs={'data-video-url': True}) + \
                                soup.find_all(attrs={'data-src': True})
                    print(f"   Elements with data-video attributes: {len(data_video)}")
                    
                    # Look for JSON with video URLs
                    import re
                    video_url_pattern = r'(https?://[^\s"\'<>]+\.(?:mp4|webm|m3u8))'
                    video_urls_in_html = re.findall(video_url_pattern, html, re.IGNORECASE)
                    print(f"   Video URLs in HTML/JS: {len(video_urls_in_html)}")
                    if video_urls_in_html:
                        print("   Sample URLs found in HTML:")
                        for vid_url in video_urls_in_html[:5]:
                            print(f"      {vid_url[:80]}")
                    
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Now run the full crawler
    print("\n3. Running full crawler...")
    video_urls = await crawler.crawl_site(url)
    
    print(f"\n4. Results:")
    print(f"   Total video URLs found: {len(video_urls)}")
    
    if video_urls:
        print("\n   Video URLs:")
        for i, vid_url in enumerate(video_urls[:20], 1):
            print(f"      {i}. {vid_url}")
    else:
        print("\n   ⚠️ No video URLs found!")
        print("\n   Suggestions:")
        print("   1. Check if the site requires JavaScript (use browser inspector)")
        print("   2. Look for API endpoints in network tab")
        print("   3. Site may use lazy loading or dynamic content")
        print("   4. Try accessing specific video pages directly")
    
    print("\n" + "=" * 80)


async def main():
    """Main test function."""
    # Test URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.hamsterix.today"
    
    await test_crawler(url)


if __name__ == "__main__":
    asyncio.run(main())
