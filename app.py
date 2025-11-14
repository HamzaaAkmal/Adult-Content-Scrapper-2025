"""Streamlit web interface for NSFW audio scraper."""

import streamlit as st
import pandas as pd
import asyncio
import os
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_pipeline import NSFWScraper
from config import NSFW_CATEGORIES

# Page configuration
st.set_page_config(
    page_title="NSFW Audio Dataset Scraper",
    page_icon="🎵",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #ff6b6b, #ee5a6f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stats-box {
        padding: 1.5rem;
        border-radius: 10px;
        background: #f0f2f6;
        margin: 1rem 0;
    }
    .category-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 15px;
        background: #4CAF50;
        color: white;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


def parse_csv_urls(uploaded_file) -> list:
    """Parse CSV file and extract URLs."""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Auto-detect URL column
        url_columns = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()]
        
        if url_columns:
            urls = df[url_columns[0]].dropna().tolist()
        elif len(df.columns) == 1:
            # Single column, assume it's URLs
            urls = df.iloc[:, 0].dropna().tolist()
        else:
            # Take first column
            urls = df.iloc[:, 0].dropna().tolist()
        
        # Clean URLs
        urls = [str(url).strip() for url in urls if str(url).strip()]
        return urls
        
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")
        return []


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🎵 NSFW Audio Dataset Scraper</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📋 How it works:
    1. **Upload CSV** with website URLs
    2. **AI crawls** each site to find video content
    3. **Whisper AI** detects NSFW audio segments
    4. **Extracts** 10-second clips automatically
    5. **Download** organized ZIP with clips & metadata
    """)
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("NSFW Categories")
        for category in NSFW_CATEGORIES:
            st.markdown(f'<span class="category-badge">{category}</span>', unsafe_allow_html=True)
        
        st.divider()
        
        st.subheader("Settings")
        st.info("✅ Groq Whisper API: Connected")
        st.info(f"🎯 Min Confidence: 0.7")
        st.info(f"⏱️ Clip Duration: 10s")
        st.info(f"🔄 Concurrent Scrapes: 10")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📤 Upload URL List")
        uploaded_file = st.file_uploader(
            "Choose a CSV file with website URLs",
            type=['csv'],
            help="CSV should contain a column with website URLs"
        )
    
    with col2:
        st.subheader("📊 Statistics")
        if 'results' in st.session_state and st.session_state.results:
            results = st.session_state.results
            st.metric("Websites Processed", results.get('total_websites', 0))
            st.metric("Videos Found", results.get('videos_found', 0))
            st.metric("Clips Extracted", results.get('clips_extracted', 0))
    
    # URL Preview
    if uploaded_file:
        urls = parse_csv_urls(uploaded_file)
        
        if urls:
            st.success(f"✅ Found {len(urls)} URLs in CSV")
            
            with st.expander("🔍 Preview URLs"):
                st.dataframe(pd.DataFrame({'URL': urls[:10]}))
                if len(urls) > 10:
                    st.info(f"... and {len(urls) - 10} more URLs")
            
            # Start scraping button
            st.divider()
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            
            with col_btn2:
                start_button = st.button(
                    "🚀 Start Scraping",
                    type="primary",
                    use_container_width=True
                )
            
            if start_button:
                run_scraping_pipeline(urls)
    
    # Results section
    if 'results' in st.session_state and st.session_state.results:
        display_results(st.session_state.results)


def run_scraping_pipeline(urls: list):
    """Run the scraping pipeline with progress tracking."""
    
    st.divider()
    st.subheader("🔄 Scraping in Progress...")
    
    # Progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.expander("📝 Detailed Log", expanded=True)
    
    def progress_callback(message: str):
        """Update UI with progress."""
        with log_container:
            st.text(message)
    
    # Run scraper
    try:
        scraper = NSFWScraper(progress_callback=progress_callback)
        
        # Create and run event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        status_text.text("🌐 Crawling websites...")
        progress_bar.progress(10)
        
        results = loop.run_until_complete(scraper.scrape_from_urls(urls))
        
        progress_bar.progress(100)
        status_text.text("✅ Scraping complete!")
        
        # Save results to session state
        st.session_state.results = results
        st.session_state.scraper = scraper
        
        st.success(f"🎉 Successfully extracted {results['clips_extracted']} clips!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during scraping: {e}")
        st.exception(e)


def display_results(results: dict):
    """Display scraping results and download options."""
    
    st.divider()
    st.header("📊 Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Websites Scraped", results.get('total_websites', 0))
    with col2:
        st.metric("Videos Found", results.get('videos_found', 0))
    with col3:
        st.metric("Videos Downloaded", results.get('videos_downloaded', 0))
    with col4:
        st.metric("Clips Extracted", results.get('clips_extracted', 0))
    
    # Statistics
    if 'statistics' in results:
        stats = results['statistics']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📁 Clips by Category")
            category_df = pd.DataFrame(
                list(stats.get('by_category', {}).items()),
                columns=['Category', 'Count']
            ).sort_values('Count', ascending=False)
            st.dataframe(category_df, use_container_width=True)
        
        with col2:
            st.subheader("🌐 Clips by Domain")
            domain_df = pd.DataFrame(
                list(stats.get('by_domain', {}).items()),
                columns=['Domain', 'Count']
            ).sort_values('Count', ascending=False)
            st.dataframe(domain_df, use_container_width=True)
        
        st.metric("Average Confidence", f"{stats.get('avg_confidence', 0):.2%}")
    
    # Clip details
    if results.get('clips_metadata'):
        st.subheader("🎵 Extracted Clips")
        
        clips_df = pd.DataFrame(results['clips_metadata'])
        
        # Select columns to display
        display_columns = ['domain', 'category', 'confidence', 'timestamp', 'text']
        display_columns = [col for col in display_columns if col in clips_df.columns]
        
        st.dataframe(
            clips_df[display_columns].head(50),
            use_container_width=True
        )
        
        if len(clips_df) > 50:
            st.info(f"Showing first 50 of {len(clips_df)} clips")
    
    # Download section
    st.divider()
    st.subheader("📥 Download")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("📦 Create Download ZIP", type="primary", use_container_width=True):
            with st.spinner("Creating ZIP archive..."):
                scraper = st.session_state.get('scraper')
                if scraper:
                    zip_path = scraper.create_download_zip()
                    
                    if zip_path and os.path.exists(zip_path):
                        with open(zip_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Download ZIP",
                                data=f,
                                file_name=os.path.basename(zip_path),
                                mime="application/zip",
                                use_container_width=True
                            )
                        st.success("✅ ZIP created successfully!")
                    else:
                        st.error("❌ Failed to create ZIP file")
                else:
                    st.error("❌ Scraper not available")
    
    # Errors section
    if results.get('errors'):
        st.divider()
        st.subheader("⚠️ Errors")
        
        errors_df = pd.DataFrame(results['errors'])
        st.dataframe(errors_df, use_container_width=True)


# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'scraper' not in st.session_state:
    st.session_state.scraper = None


if __name__ == "__main__":
    main()
