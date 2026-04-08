from dataclasses import dataclass

@dataclass
class RegisterGroupRequest:
    chat_id: int
    title: str
    owner_id: int
    invite_link: str
    require_approval: bool
    member_count: int
    language: str
    chat_type: str    # 'channel', 'group' o 'supergroup'
    status: str = "pending"