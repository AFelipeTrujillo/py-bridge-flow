import asyncio
import logging
from typing import List
from src.Domain.Repository.GroupRepository import GroupRepository
from src.Domain.Entity.Group import Group

logger = logging.getLogger(__name__)

class DailyBroadcast:
    """UseCase to handle the daily distribution of group links."""

    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def execute(self, bot) -> None:
        groups = await self.repository.get_all_active()
        if not groups:
            return

        # Prepare messages by language
        messages = {
            "en": "🌟 **Join our partner groups!**\n\n",
            "es": "🌟 **¡Únete a nuestros grupos amigos!**\n\n"
        }

        for group in groups:
            lang = group.language if group.language in messages else "en"
            messages[lang] += f"• [{group.title}]({group.invite_link})\n"

        # Send to each group
        for target_group in groups:
            try:
                content = messages.get(target_group.language, messages["en"])
                await bot.send_message(
                    chat_id=target_group.chat_id,
                    text=content,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                # Anti-spam delay to respect Telegram Rate Limits
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Failed to send broadcast to {target_group.chat_id}: {e}")