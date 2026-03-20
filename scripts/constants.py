from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")

def now():
    """Return current time in the project timezone."""
    return datetime.now(TZ)

IMAGE_DIR = Path("data/images")