from typing import Optional
from src.Domain.Entity.User import User
from src.Domain.Repository.UserRepository import UserRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoUserRepository(UserRepository):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.collection = database.get_collection("users")

    async def save(self, user: User) -> None:
        user_data = {
            "user_id": user.user_id,
            "first_name": user.first_name,
            "username": user.username,
            "language": user.language,
            "created_at": user.created_at
        }
        await self.collection.update_one(
            {"user_id": user.user_id},
            {"$set": user_data},
            upsert=True
        )

    async def find_by_id(self, user_id: int) -> Optional[User]:
        doc = await self.collection.find_one({"user_id": user_id})
        if not doc:
            return None
        return User(
            user_id=doc["user_id"],
            first_name=doc["first_name"],
            username=doc.get("username"),
            language=doc.get("language", "en"),
            created_at=doc.get("created_at")
        )