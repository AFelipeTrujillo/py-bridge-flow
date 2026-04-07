from abc import ABC, abstractmethod
from typing import List, Optional
from src.Domain.Entity.Group import Group

class GroupRepository(ABC):
    """Interface for Group persistence."""

    @abstractmethod
    async def save(self, group: Group) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, chat_id: int) -> Optional[Group]:
        pass

    @abstractmethod
    async def get_all_active(self) -> List[Group]:
        pass

    @abstractmethod
    async def update_stats(self, chat_id: int, member_count: int, joins: int) -> None:
        pass