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
