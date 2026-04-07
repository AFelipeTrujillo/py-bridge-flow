import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.Application.UseCase.GetWelcomeMessage import GetWelcomeMessage
from src.Application.UseCase.UpdateUserPreference import UpdateUserPreference

logger = logging.getLogger(__name__)


class StartHandler:
    def __init__(
            self,
            welcome_use_case: GetWelcomeMessage,
            update_user_use_case: UpdateUserPreference
    ):
        self.welcome_use_case = welcome_use_case
        self.update_user_use_case = update_user_use_case

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start inicial."""
        user = update.effective_user

        if update.effective_chat.type != "private":
            return

        text = await self.welcome_use_case.execute(user.first_name)

        keyboard = [
            [
                InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en"),
                InlineKeyboardButton("Español 🇪🇸", callback_data="setlang_es")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la pulsación de los botones de idioma (setlang_)."""
        query = update.callback_query
        user = update.effective_user
        bot_username = context.bot.username

        _, lang = query.data.split("_")

        await self.update_user_use_case.execute(
            user_id=user.id,
            first_name=user.first_name,
            lang=lang,
            username=user.username
        )

        if lang == "en":
            confirm_text = (
                f"✅ **Language set to English!**\n\n"
                f"Now, go to your group and add me as an admin by searching for:\n\n"
                f"`@{bot_username}`"
            )
        else:
            confirm_text = (
                f"✅ **¡Idioma configurado en Español!**\n\n"
                f"Ahora, ve a tu grupo y añádeme como administrador buscando mi usuario:\n\n"
                f"`@{bot_username}`"
            )

        await query.answer("Success! / ¡Logrado!")
        await query.edit_message_text(text=confirm_text, parse_mode="Markdown")

        logger.info(f"User {user.id} set language preference to {lang}")