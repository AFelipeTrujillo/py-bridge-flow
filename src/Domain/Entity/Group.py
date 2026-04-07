from dataclasses import dataclass, field
from datetime import datetime
from src.Domain.ValueObject.LinkSettings import LinkSettings

@dataclass
class Group:
    """Represents a Telegram Group registered in the system."""
    chat_id: int
    title: str
    owner_id: int
    invite_link: str
    settings: LinkSettings
    language: str  # 'en' for English, 'es' for Spanish
    member_count: int = 0
    joined_via_bot_count: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def update_metrics(self, current_total: int):
        """Updates the total member count of the group."""
        self.member_count = current_total