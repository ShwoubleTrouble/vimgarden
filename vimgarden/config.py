"""Configuration constants for vimgarden."""
from pathlib import Path

MIN_COLS = 80
MIN_LINES = 24

SAVE_DIR = Path.home() / ".local" / "share" / "vimgarden"
SAVE_FILE = SAVE_DIR / "save.json"
BACKUP_SAVE_FILE = SAVE_DIR / "save.json.bak"

TICK_TIMEOUT_MS = 100
AUTO_SAVE_INTERVAL = 60.0
MAX_OFFLINE_SECONDS = 7 * 86400.0  # 7 days max catch-up
WILT_GRACE_BUFFER_SECONDS = 3600.0  # 1 hour grace before dying when recovering from offline

# Multi-pot shelf settings
DEFAULT_UNLOCKED_POTS = 3
MAX_POTS = 5
POT_PRICE = 75

# Seasons & Weather
SEASON_DURATION = 180.0   # 3 minutes per season
WEATHER_DURATION = 60.0   # 1 minute per weather state

# Tools & Supplies
FERTILIZER_PRICE = 15
FERTILIZER_BOOST_SECONDS = 90.0
FERTILIZER_SPEED_MULT = 1.5

