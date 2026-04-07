from telegram import Update
from telegram.ext import ContextTypes
from src.Application.UseCase.GetWelcomeMessage import GetWelcomeMessage


class StartHandler:
    def __init__(self, use_case: GetWelcomeMessage):
        self.use_case = use_case

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responds to the /start command."""
        user = update.effective_user

        # We only want to show the welcome message in Private Chats
        if update.effective_chat.type != "private":
            return

        message = await self.use_case.execute(user.first_name)
        await update.message.reply_text(message, parse_mode="Markdown")