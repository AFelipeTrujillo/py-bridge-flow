from dataclasses import dataclass

@dataclass(frozen=True)
class LinkSettings:
    """Settings for the generated invite link."""
    require_approval: bool = True
    expire_date: int = None  # Unix timestamp if needed
    member_limit: int = None