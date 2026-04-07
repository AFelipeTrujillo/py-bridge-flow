from dataclasses import dataclass

@dataclass(frozen=True)
class RegisterGroupRequest:
    """Input data needed to register a group."""
    chat_id: int
    title: str
    owner_id: int
    invite_link: str
    require_approval: bool
    member_count: int
    language: str  # Added field