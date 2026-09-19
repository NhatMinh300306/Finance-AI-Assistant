"""
Security utilities.
Placeholder for future authentication implementation.
"""

from datetime import datetime, timezone


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


# Future: JWT token creation/verification, password hashing, etc.
# This module is structured to easily add authentication later.
