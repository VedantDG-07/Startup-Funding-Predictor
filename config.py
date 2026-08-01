"""
config.py – Centralized configuration for StartupIQ.
Reads credentials from environment / .env file, with sensible defaults.
"""
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Config:
    """Application-wide configuration loaded from environment variables."""

    # ── Database ──────────────────────────────────────────────────────────────
    DB_HOST:     str = os.getenv("DB_HOST", "localhost")
    DB_PORT:     int = int(os.getenv("DB_PORT", 3306))
    DB_USER:     str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME:     str = os.getenv("DB_NAME", "startup_db")

    # ── Flask ─────────────────────────────────────────────────────────────────
    SECRET_KEY:  str = os.getenv("SECRET_KEY", "startupiq-dev-secret")
    DEBUG:       bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    HOST:        str = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT:        int = int(os.getenv("FLASK_PORT", 5000))

    # ── Scraping ──────────────────────────────────────────────────────────────
    REQUEST_TIMEOUT:  int = int(os.getenv("REQUEST_TIMEOUT", 10))
    REQUEST_DELAY:    float = float(os.getenv("REQUEST_DELAY", 1.0))
    MAX_RETRIES:      int = int(os.getenv("MAX_RETRIES", 3))
