import re
import logging
from datetime import datetime
from dateutil import parser
from rich.logging import RichHandler

def setup_logger(name: str = "geoscope"):
    """
    Configures a Rich-based logger for the application.
    """
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger(name)

logger = setup_logger()

def parse_flexible_date(date_str: str) -> datetime:
    """
    Parses various date string formats into a standard datetime object.
    Handles ISO, RFC, and common scraper outputs.
    """
    if not date_str:
        return datetime.utcnow()
    
    try:
        # dateutil handles most fuzzy parsing automatically
        return parser.parse(date_str, fuzzy=True)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: '{date_str}'. Defaulting to NOW.")
        return datetime.utcnow()

def clean_text(text: str) -> str:
    """
    Normalizes text for the SLM:
    - Removes excessive whitespace/newlines.
    - Strips HTML tags (basic).
    - Removes non-printable characters.
    """
    if not text:
        return ""
    
    # Remove HTML tags (if any slipped through newspaper3k)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace multiple newlines/tabs with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing
    return text.strip()

def extract_hashtags(text: str) -> list[str]:
    """
    Extracts hashtags from raw text for keyword indexing.
    """
    return re.findall(r"#(\w+)", text)