"""vimgarden package."""
import subprocess
from typing import Optional

__version__ = "0.2.0"
_CACHED_VERSION: Optional[str] = None


def get_version_string() -> str:
    """Return formatted version string like 'v0.2.0' with optional git commit hash."""
    global _CACHED_VERSION
    if _CACHED_VERSION is not None:
        return _CACHED_VERSION

    base = f"v{__version__}"
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.0,
        ).strip()
        if commit:
            _CACHED_VERSION = f"{base} ({commit})"
            return _CACHED_VERSION
    except Exception:
        pass

    _CACHED_VERSION = base
    return _CACHED_VERSION
