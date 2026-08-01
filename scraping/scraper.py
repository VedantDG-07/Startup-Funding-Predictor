"""
StartupIQ - Web Scraping Engine (scraping/scraper.py)
Automated collector for startup profiles, news, funding press releases, and metadata
using requests and BeautifulSoup with logging to database.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from bs4 import BeautifulSoup
from database.insert_data import log_scraping_activity, insert_startup


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class StartupScraper:
    """
    Robust web scraping client for collecting public startup intelligence and text corpus.
    """

    def __init__(self, timeout: int = 10, delay: float = 1.0):
        self.timeout = timeout
        self.delay = delay
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36 StartupIQ-Scraper/1.0"
            )
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a given web URL safely.
        """
        try:
            time.sleep(self.delay)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.text
            else:
                logging.warning(f"HTTP {response.status_code} received for URL: {url}")
                return None
        except Exception as e:
            logging.error(f"Error fetching URL {url}: {e}")
            return None

    def parse_startup_profile(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """
        Extract structured startup metadata and text corpus from raw HTML.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title / company name
        name_tag = soup.find("h1") or soup.find("title")
        name = name_tag.get_text(strip=True) if name_tag else "Unknown Startup"

        # Extract meta description / paragraph summaries
        meta_desc = soup.find("meta", attrs={"name": "description"})
        short_desc = meta_desc["content"] if meta_desc and "content" in meta_desc.attrs else ""

        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
        long_desc = " ".join(paragraphs[:5]) if paragraphs else short_desc

        return {
            "name": name,
            "domain": source_url,
            "industry": "Technology",
            "operating_status": "operating",
            "short_description": short_desc or long_desc[:250],
            "long_description": long_desc,
            "source_url": source_url
        }

    def run_pipeline(self, target_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Execute scraping run across target URLs and record activity logs.
        """
        scraped_records = []
        log_id = log_scraping_activity("web_scraper_requests", target_urls[0] if target_urls else None, "in_progress", 0)

        success_count = 0
        for url in target_urls:
            html = self.fetch_page(url)
            if html:
                profile = self.parse_startup_profile(html, url)
                scraped_records.append(profile)
                success_count += 1

        status_str = "success" if success_count > 0 else "failed"
        log_scraping_activity("web_scraper_requests", target_urls[0] if target_urls else None, status_str, success_count)

        logging.info(f"Scraping run finished. Successfully parsed {success_count}/{len(target_urls)} pages.")
        return scraped_records


if __name__ == "__main__":
    scraper = StartupScraper()
    test_urls = ["https://news.ycombinator.com", "https://example.com"]
    results = scraper.run_pipeline(test_urls)
    logging.info(f"Sample Scraped Output: {results}")
