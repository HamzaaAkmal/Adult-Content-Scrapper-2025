"""Intelligent web crawler for discovering video URLs."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Set
import logging
from config import VIDEO_KEYWORDS, VIDEO_EXTENSIONS, USER_AGENT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebCrawler:
    """Crawls websites to find video URLs."""
    
    def __init__(self, max_depth: int = 3, max_urls_per_site: int = 100):
        self.max_depth = max_depth
        self.max_urls_per_site = max_urls_per_site
        self.visited_urls: Set[str] = set()
        self.video_page_patterns = [
            r'/video[s]?/',
            r'/watch/',
            r'/player/',
            r'/embed/',
            r'/v/',
            r'/clip[s]?/',
            r'/media/',
            r'/content/',
            r'\?v=',
            r'/play/',
            r'/movie[s]?/',
        ]
        
    async def crawl_site(self, base_url: str) -> List[str]:
        """Crawl a website to find video URLs."""
        logger.info(f"Starting crawl of {base_url}")
        video_urls = []
        
        async with aiohttp.ClientSession() as session:
            to_visit = [(base_url, 0)]
            
            while to_visit and len(video_urls) < self.max_urls_per_site:
                current_url, depth = to_visit.pop(0)
                
                if current_url in self.visited_urls or depth > self.max_depth:
                    continue
                    
                self.visited_urls.add(current_url)
                
                try:
                    videos, links = await self._scrape_page(session, current_url, base_url)
                    video_urls.extend(videos)
                    
                    # Add new links to visit
                    if depth < self.max_depth:
                        for link in links:
                            if link not in self.visited_urls:
                                to_visit.append((link, depth + 1))
                                
                except Exception as e:
                    logger.error(f"Error crawling {current_url}: {e}")
                    
                await asyncio.sleep(0.5)  # Rate limiting
                
        logger.info(f"Found {len(video_urls)} video URLs from {base_url}")
        
        # Log summary of what was found
        video_pages = sum(1 for url in video_urls if '/video' in url.lower())
        direct_videos = len(video_urls) - video_pages
        logger.info(f"  → {video_pages} video pages, {direct_videos} direct video files")
        
        return list(set(video_urls))[:self.max_urls_per_site]
    
    async def _scrape_page(self, session: aiohttp.ClientSession, url: str, base_url: str) -> tuple:
        """Scrape a single page for video URLs and links."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            async with session.get(url, headers=headers, timeout=20, ssl=False) as response:
                if response.status != 200:
                    logger.debug(f"Non-200 status {response.status} for {url}")
                    return [], []
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                video_urls = self._extract_video_urls(soup, url, html)
                page_links = self._extract_page_links(soup, url, base_url)
                
                logger.debug(f"Found {len(video_urls)} videos and {len(page_links)} links on {url}")
                
                return video_urls, page_links
        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
            return [], []
    
    def _extract_video_urls(self, soup: BeautifulSoup, base_url: str, html_content: str = "") -> List[str]:
        """Extract potential video URLs from page."""
        video_urls = set()  # Use set to avoid duplicates
        thumbnail_patterns = ['/thumb-', '/preview', '/sample', 't.mp4', 't.av1', 't.webm', '526x298', '350x620']
        
        # 1. Check video tags
        for video in soup.find_all(['video', 'source']):
            for attr in ['src', 'data-src', 'data-video', 'data-video-src']:
                src = video.get(attr)
                if src and not any(pattern in src for pattern in thumbnail_patterns):
                    video_urls.add(urljoin(base_url, src))
        
        # 2. Check iframes (embedded videos)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src') or iframe.get('data-src')
            if src:
                # Skip Google Tag Manager and analytics iframes
                if 'googletagmanager' not in src and 'analytics' not in src:
                    video_urls.add(urljoin(base_url, src))
        
        # 3. Check links with video extensions or video-like URLs
        for link in soup.find_all('a', href=True):
            href = link['href']
            href_lower = href.lower()
            
            # Direct video file links (but skip thumbnails)
            if any(href_lower.endswith(ext) for ext in VIDEO_EXTENSIONS):
                if not any(pattern in href for pattern in thumbnail_patterns):
                    video_urls.add(urljoin(base_url, href))
            
            # Video page URLs (likely contain videos) - these are the most important
            elif any(re.search(pattern, href_lower) for pattern in self.video_page_patterns):
                full_url = urljoin(base_url, href)
                if self._is_video_page_url(full_url) and '#' not in href:
                    video_urls.add(full_url)
        
        # 4. Check meta tags
        for meta in soup.find_all('meta'):
            property_attr = meta.get('property', '').lower()
            name_attr = meta.get('name', '').lower()
            
            if any(tag in property_attr or tag in name_attr for tag in ['og:video', 'twitter:player', 'video:url']):
                content = meta.get('content') or meta.get('value')
                if content and not any(pattern in content for pattern in thumbnail_patterns):
                    video_urls.add(urljoin(base_url, content))
        
        # 5. Check data attributes (lazy loading) - but skip thumbnails
        for attr in ['data-video-url', 'data-video', 'data-src', 'data-video-src', 'data-href', 'data-mp4']:
            for elem in soup.find_all(attrs={attr: True}):
                src = elem.get(attr)
                if src and not any(pattern in src for pattern in thumbnail_patterns):
                    video_urls.add(urljoin(base_url, src))
        
        # 6. Look for FULL video URLs in JavaScript/JSON (skip thumbnails)
        if html_content:
            # Find URLs that look like videos in the HTML
            video_url_patterns = [
                r'"videoUrl"\s*:\s*"(https?://[^"]+\.(?:mp4|webm)[^"]*)"',
                r'"url"\s*:\s*"(https?://[^"]+\.(?:mp4|webm|m3u8)[^"]*)"',
                r'"file"\s*:\s*"(https?://[^"]+\.(?:mp4|webm|m3u8)[^"]*)"',
                r'file:\s*["\']([^"\']+\.(?:mp4|webm|m3u8)[^"\']*)["\']',
                r'src:\s*["\']([^"\']+\.(?:mp4|webm|m3u8)[^"\']*)["\']',
            ]
            
            for pattern in video_url_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if not any(thumb in match for thumb in thumbnail_patterns):
                        video_urls.add(match)
        
        # 7. Check for HLS/DASH manifests
        for link in soup.find_all('link', rel=True):
            href = link.get('href', '')
            if any(ext in href.lower() for ext in ['.m3u8', '.mpd']):
                video_urls.add(urljoin(base_url, href))
        
        # Filter out obvious non-video URLs
        filtered_urls = []
        for url in video_urls:
            # Skip thumbnails
            if any(pattern in url for pattern in thumbnail_patterns):
                continue
            # Skip tiny preview files
            if re.search(r'\d+x\d+', url) and not any(ext in url for ext in ['.m3u8', '.mpd']):
                continue
            filtered_urls.append(url)
        
        return filtered_urls
    
    def _extract_page_links(self, soup: BeautifulSoup, current_url: str, base_url: str) -> List[str]:
        """Extract relevant page links to crawl."""
        links = []
        base_domain = urlparse(base_url).netloc
        current_path = urlparse(current_url).path
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only follow links on the same domain
            if parsed.netloc != base_domain:
                continue
            
            # Skip already visited
            if full_url in self.visited_urls:
                continue
            
            # Skip anchors and query-only changes
            if parsed.fragment and parsed.path == current_path:
                continue
            
            href_lower = href.lower()
            link_text = link.get_text().lower()
            full_path = parsed.path.lower()
            
            # Priority 1: Video-related URLs
            if any(re.search(pattern, full_path) for pattern in self.video_page_patterns):
                links.insert(0, full_url)  # Add to front
                continue
            
            # Priority 2: Links with video keywords
            if any(keyword in link_text or keyword in href_lower for keyword in VIDEO_KEYWORDS):
                links.insert(0, full_url)
                continue
            
            # Priority 3: Category/archive pages (often contain video listings)
            if any(term in full_path for term in ['/category', '/archive', '/gallery', '/collection', '/list']):
                links.append(full_url)
                continue
            
            # Add other same-domain links with lower priority
            if len(links) < 50:  # Limit total links
                links.append(full_url)
                
        return links[:30]  # Return top 30 most relevant
    
    def _is_video_page_url(self, url: str) -> bool:
        """Check if URL likely points to a video page."""
        path = urlparse(url).path.lower()
        return any(re.search(pattern, path) for pattern in self.video_page_patterns)


async def crawl_multiple_sites(urls: List[str]) -> dict:
    """Crawl multiple sites concurrently."""
    crawler = WebCrawler()
    results = {}
    
    tasks = [crawler.crawl_site(url) for url in urls]
    site_videos = await asyncio.gather(*tasks, return_exceptions=True)
    
    for url, videos in zip(urls, site_videos):
        if isinstance(videos, Exception):
            logger.error(f"Failed to crawl {url}: {videos}")
            results[url] = []
        else:
            results[url] = videos
            
    return results
