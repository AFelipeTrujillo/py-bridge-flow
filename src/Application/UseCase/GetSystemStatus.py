from dataclasses import dataclass
from src.Domain.Repository.GroupRepository import GroupRepository

@dataclass(frozen=True)
class SystemStatusDTO:
    """Snapshot of the system's current state."""
    total_groups: int
    active_groups: int
    database_status: str

class GetSystemStatus:
    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def execute(self) -> SystemStatusDTO:
        try:
            all_groups = await self.repository.get_all_active()
            return SystemStatusDTO(
                total_groups=len(all_groups),
                active_groups=sum(1 for g in all_groups if g.is_active),
                database_status="Connected"
            )
        except Exception:
            return SystemStatusDTO(0, 0, "Disconnected")