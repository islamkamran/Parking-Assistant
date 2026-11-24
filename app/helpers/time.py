from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time without tzinfo (MySQL DATETIME columns don't store time zones)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
