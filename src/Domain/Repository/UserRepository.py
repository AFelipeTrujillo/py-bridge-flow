from abc import ABC, abstractmethod
from typing import Optional
from src.Domain.Entity.User import User

class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass