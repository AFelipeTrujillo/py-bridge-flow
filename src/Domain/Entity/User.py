from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class User:
    """Represents a Telegram User interacting with the bot."""
    user_id: int
    first_name: str
    username: str = None
    language: str = "en"  # Default to English
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )