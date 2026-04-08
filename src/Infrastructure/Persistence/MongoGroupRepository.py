from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.Domain.Entity.Group import Group
from src.Domain.ValueObject.LinkSettings import LinkSettings
from src.Domain.Repository.GroupRepository import GroupRepository


class MongoGroupRepository(GroupRepository):
    """
    MongoDB implementation of the Group Repository.
    Adapts the Domain Entity to the Persistence layer.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        # We use a collection named 'groups'
        self.collection = database.get_collection("groups")

    async def save(self, group: Group) -> None:
        """Saves or updates a group document."""
        group_data = {
            "chat_id": group.chat_id,
            "title": group.title,
            "owner_id": group.owner_id,
            "invite_link": group.invite_link,
            "language": group.language,
            "member_count": group.member_count,
            "joined_via_bot_count": group.joined_via_bot_count,
            "is_active": bool(group.is_active),
            "status": group.status,
            "created_at": group.created_at,
            "settings": {
                "require_approval": group.settings.require_approval,
                "expire_date": group.settings.expire_date,
                "member_limit": group.settings.member_limit
            }
        }

        # Using upsert=True to create if it doesn't exist or update if it does
        await self.collection.update_one(
            {"chat_id": group.chat_id},
            {"$set": group_data},
            upsert=True
        )

    async def find_by_id(self, chat_id: int) -> Optional[Group]:
        """Retrieves a group by its Telegram chat_id."""
        doc = await self.collection.find_one({"chat_id": chat_id})
        if not doc:
            return None

        return self._map_to_entity(doc)

    async def get_all_active(self) -> List[Group]:
        """Retrieves all active groups for broadcast."""
        cursor = self.collection.find({"is_active": True})
        groups = []
        async for doc in cursor:
            groups.append(self._map_to_entity(doc))
        return groups

    async def update_stats(self, chat_id: int, member_count: int, joins: int) -> None:
        """Updates specific metrics without overwriting the whole entity."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {
                "$set": {"member_count": member_count},
                "$inc": {"joined_via_bot_count": joins}
            }
        )

    async def find_by_owner(self, owner_id: int) -> list[Group]:
        cursor = self.collection.find({"owner_id": owner_id})
        groups = []
        async for doc in cursor:
            groups.append(Group(
                chat_id=doc["chat_id"],
                title=doc["title"],
                owner_id=doc["owner_id"],
                invite_link=doc.get("invite_link"),
                is_active=doc.get("is_active", True),
                language=doc.get("language", "en"),
                settings=LinkSettings(**doc["settings"]) if "settings" in doc else LinkSettings()
            ))
        return groups

    async def update_status(self, chat_id: int, new_status: str):
        """Actualiza el estado de moderación de un grupo."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": new_status}}
        )

    def _map_to_entity(self, doc: dict) -> Group:
        """Internal helper to convert a Mongo document to a Domain Entity."""
        settings_doc = doc.get("settings", {})
        settings = LinkSettings(
            require_approval=settings_doc.get("require_approval", True),
            expire_date=settings_doc.get("expire_date"),
            member_limit=settings_doc.get("member_limit")
        )

        return Group(
            chat_id=doc["chat_id"],
            title=doc["title"],
            owner_id=doc["owner_id"],
            invite_link=doc["invite_link"],
            language=doc.get("language", "en"),
            settings=settings,
            member_count=doc.get("member_count", 0),
            joined_via_bot_count=doc.get("joined_via_bot_count", 0),
            is_active=doc.get("is_active", True),
            created_at=doc.get("created_at")
        )