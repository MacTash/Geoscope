import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Define Base Paths
# BASE_DIR resolves to the root of your project (the folder containing requirements.txt)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Automatically create the 'data' directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    # Metadata
    APP_NAME = "Geoscope CLI"
    VERSION = "1.0.0-Beta"
    
    # Paths
    DATA_DIR = DATA_DIR

    # AI / Ollama Settings
    # Defaults to localhost and llama3.2:3b if not set in .env
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:3b")

    # Database Settings
    # Stores the SQLite DB inside the 'data' folder
    DB_NAME = os.getenv("DB_NAME", "geoscope.db")
    DB_URL = f"sqlite:///{DATA_DIR}/{DB_NAME}"

    # Scraping / Network Settings
    # High-quality User-Agent to avoid being blocked by Google News or RSS feeds
    USER_AGENT = os.getenv(
        "USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Export as a singleton instance
settings = Config()