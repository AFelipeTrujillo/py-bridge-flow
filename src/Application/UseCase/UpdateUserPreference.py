from src.Domain.Entity.User import User
from src.Domain.Repository.UserRepository import UserRepository


class UpdateUserPreference:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user_id: int, first_name: str, lang: str, username: str = None):
        user = await self.repository.find_by_id(user_id)

        if not user:
            user = User(user_id=user_id, first_name=first_name, username=username, language=lang)
        else:
            user.language = lang

        await self.repository.save(user)
        return user