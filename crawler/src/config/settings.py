import os
from pathlib import Path
import yaml

# Project Roots
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = ROOT_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
FILTERED_DIR = DATA_DIR / "filtered"
DATASET_DIR = DATA_DIR / "dataset"

STYLES_CONFIG_PATH = Path(__file__).parent / "styles_config.yaml"

# Global Config
TIMEOUT = 15
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1.0  # seconds

def load_styles_config():
    if not STYLES_CONFIG_PATH.exists():
        return {}
    with open(STYLES_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

STYLES_CONFIG = load_styles_config()
STYLES = STYLES_CONFIG.get("styles", {})
AI_BLACKLIST_KEYWORDS = STYLES_CONFIG.get("ai_blacklist_keywords", [])
NEGATIVE_KEYWORDS = STYLES_CONFIG.get("negative_keywords", [])
