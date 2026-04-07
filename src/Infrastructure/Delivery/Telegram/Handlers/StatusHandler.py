import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.Application.UseCase.GetSystemStatus import GetSystemStatus
from src.Infrastructure.Config.Settings import settings

logger = logging.getLogger(__name__)


class StatusHandler:
    def __init__(self, use_case: GetSystemStatus):
        self.use_case = use_case

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responds with system health, only for the bot creator."""
        user_id = update.effective_user.id

        # Admin Filter Logic
        if user_id != settings.ADMIN_ID:
            logger.warning(f"Unauthorized access attempt to /status by user {user_id}")
            # Optional: Silent fail or polite rejection
            return

        status = await self.use_case.execute()

        message = (
            "🛡️ **Admin Dashboard**\n"
            "--------------------------\n"
            f"📊 **Groups:** {status.total_groups}\n"
            f"🟢 **Active:** {status.active_groups}\n"
            f"🗄️ **DB Status:** `{status.database_status}`\n"
            f"🕒 **UTC Time:** `{update.message.date.strftime('%H:%M:%S')}`"
        )

        await update.message.reply_text(message, parse_mode="Markdown")