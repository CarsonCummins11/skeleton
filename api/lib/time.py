import time
from datetime import datetime


def usec_timestamp() -> int:
    """
    Returns the current time in microseconds since the epoch.
    """
    return int(time.time() * 1_000_000)


def format_timestamp(timestamp):
    """Format a timestamp (microseconds since epoch) to a readable date"""
    if timestamp is None:
        return "Never"
    try:
        # Convert microseconds to seconds
        dt = datetime.fromtimestamp(timestamp / 1000000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(timestamp)
