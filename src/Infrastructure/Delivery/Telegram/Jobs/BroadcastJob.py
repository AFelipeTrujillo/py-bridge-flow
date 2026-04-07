import logging
from datetime import time
from telegram.ext import ContextTypes
from src.Application.UseCase.DailyBroadcast import DailyBroadcast

logger = logging.getLogger(__name__)


class BroadcastJob:
    """Manager for scheduled background tasks."""

    def __init__(self, broadcast_use_case: DailyBroadcast):
        self.use_case = broadcast_use_case

    async def run_daily_broadcast(self, context: ContextTypes.DEFAULT_TYPE):
        """Job callback that triggers the Use Case."""
        logger.info("Starting scheduled daily broadcast...")

        # We pass the bot instance to the Use Case to perform the sending logic
        await self.use_case.execute(context.bot)

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