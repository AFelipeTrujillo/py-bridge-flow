import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.Domain.Repository.GroupRepository import GroupRepository

logger = logging.getLogger(__name__)

class MemberHandler:
    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def on_join_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered when a user requests to join a group via an admin-approval link."""
        request = update.chat_join_request
        chat_id = request.chat.id

        # Increment the 'joined_via_bot' counter in the DB
        # We don't need a complex Use Case for a simple counter increment
        await self.repository.update_stats(
            chat_id=chat_id,
            member_count=await request.chat.get_member_count(),
            joins=1
        )

        logger.info(f"New join request in {chat_id}. Metrics updated.")