import os
import sys
import time
import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# Path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.logger import logger
from scraping.scraper import StartupScraper
from database.db_helper import get_connection, close_connection

# Seed categories for generating realistic crawl data
INDUSTRIES = [
    "Fintech", "Artificial Intelligence", "Healthtech", "E-commerce",
    "Edtech", "Clean Energy", "Cybersecurity", "SaaS", "Biotech", "Logistics"
]
COUNTRIES = ["United States", "India", "United Kingdom", "Germany", "Singapore", "Canada", "Israel"]
STATUSES = ["operating", "acquired", "closed", "ipo"]

class BaseExtractorSource(ABC):
    """
    Abstract Base Class for ETL extraction sources.
    Allows additional startup directories or APIs to be plugged in.
    """
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        pass


class HackerNewsAPIExtractorSource(BaseExtractorSource):
    """
    Real-time Extractor Source querying HackerNews Algolia REST API for startup launches and funding stories.
    """
    def __init__(self, limit: int = 30, query: str = "funding"):
        self.limit = limit
        self.query = query
        self.scraper = StartupScraper(delay=0.2)

    def extract(self) -> List[Dict[str, Any]]:
        logger.info(f"Executing real online extraction from HackerNews API (Query: '{self.query}', Limit: {self.limit})...")
        records = self.scraper.fetch_hn_funding_stories(query=self.query, limit=self.limit)
        logger.info(f"HackerNews API Extractor retrieved {len(records)} real records.")
        return records


class WebDirectoryScraperSource(BaseExtractorSource):
    """
    Live Scraper Source that fetches real online startup profiles and news via TechCrunch Startups feed.
    """
    def __init__(self, limit: int = 30, start_page: int = 1, end_page: int = 1, page_size: int = 30):
        self.limit = limit
        self.scraper = StartupScraper(delay=0.5)

    def extract(self) -> List[Dict[str, Any]]:
        logger.info(f"Executing real online extraction from TechCrunch Web Directory Scraper...")
        records = self.scraper.fetch_techcrunch_feed(limit=self.limit)
        logger.info(f"Web Directory Scraper retrieved {len(records)} real records.")
        return records


class SeedExtractorSource(BaseExtractorSource):
    """
    Fallback Extractor Source combining real HackerNews launches and tech directory articles.
    """
    def __init__(self, target_num: int = 30):
        self.target_num = target_num
        self.scraper = StartupScraper(delay=0.2)

    def extract(self) -> List[Dict[str, Any]]:
        logger.info("Executing extraction from Seed Data Source (HackerNews Show HN)...")
        records = self.scraper.fetch_hn_funding_stories(query="startup", limit=self.target_num)
        logger.info(f"Seed Data Source extracted {len(records)} real records.")
        return records


class ExtractorOrchestrator:
    """
    Coordinates list of active extractor sources to pool incoming raw data.
    """
    def __init__(self, sources: Optional[List[BaseExtractorSource]] = None):
        self.sources = sources or []

    def add_source(self, source: BaseExtractorSource):
        self.sources.append(source)

    def run_all(self) -> List[Dict[str, Any]]:
        all_records = []
        for src in self.sources:
            try:
                records = src.extract()
                all_records.extend(records)
            except Exception as e:
                logger.error(f"Error in extractor source {src.__class__.__name__}: {e}")
        logger.info(f"Total extracted records across all sources: {len(all_records)}")
        return all_records


if __name__ == "__main__":
    orchestrator = ExtractorOrchestrator()
    orchestrator.add_source(HackerNewsAPIExtractorSource(limit=10))
    orchestrator.add_source(WebDirectoryScraperSource(limit=10))
    res = orchestrator.run_all()
    print(f"Total real online records extracted: {len(res)}")

