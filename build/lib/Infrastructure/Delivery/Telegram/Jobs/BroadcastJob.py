import logging
from datetime import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.Application.UseCase.DailyBroadcast import DailyBroadcast
from src.Domain.Repository.GroupRepository import GroupRepository  # Importante para buscar destinos

logger = logging.getLogger(__name__)


class BroadcastJob:
    """Manager for scheduled background tasks."""

    def __init__(self, broadcast_use_case: DailyBroadcast, group_repo: GroupRepository):
        self.use_case = broadcast_use_case
        self.group_repo = group_repo  # Necesitamos el repo para saber a qué grupos enviar

    async def run_daily_broadcast(self, context: ContextTypes.DEFAULT_TYPE):
        """Job callback that triggers the Use Case per language."""
        logger.info("Starting scheduled daily broadcast...")

        targets = await self.group_repo.get_all_active()

        if not targets:
            logger.warning("No active groups found to receive the broadcast.")
            return

        bot_username = (await context.bot.get_me()).username
        start_url = f"https://t.me/{bot_username}?start=setup"

        msg_es = await self.use_case.execute(lang="es")
        msg_en = await self.use_case.execute(lang="en")

        btn_es = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Registra tu grupo", url=start_url)
        ]])

        btn_en = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Register your group", url=start_url)
        ]])

        for target in targets:
            if target.language == "es":
                text = msg_es
                reply_markup = btn_es
            else:
                text = msg_en
                reply_markup = btn_en

            try:
                await context.bot.send_message(
                    chat_id=target.chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Error enviando broadcast: {e}")

        logger.info("Daily broadcast completed successfully.")

    def schedule(self, job_queue, broadcast_time_str: str):
        """Schedules the job based on the time string (HH:MM) from Settings."""
        try:
            hour, minute = map(int, broadcast_time_str.split(":"))
            scheduled_time = time(hour=hour, minute=minute)

            job_queue.run_daily(
                self.run_daily_broadcast,
                time=scheduled_time,
                name="daily_broadcast_job"
            )
            logger.info(f"Broadcast scheduled daily at {broadcast_time_str} UTC.")
        except ValueError as e:
            logger.error(f"Invalid BROADCAST_TIME_UTC format: {e}")