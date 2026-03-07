from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")

def now():
    """Return current time in the project timezone."""
    return datetime.now(TZ)