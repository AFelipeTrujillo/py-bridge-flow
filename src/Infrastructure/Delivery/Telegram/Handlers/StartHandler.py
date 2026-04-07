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

        # Solo respondemos en chats privados
        if update.effective_chat.type != "private":
            return

        # Obtenemos el mensaje bilingüe inicial del Caso de Uso
        text = await self.welcome_use_case.execute(user.first_name)

        # Creamos los botones de selección de idioma
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

        # Extraemos el idioma del callback_data (ej: setlang_es -> es)
        _, lang = query.data.split("_")

        # Ejecutamos el Caso de Uso para guardar/actualizar al usuario en la DB
        await self.update_user_use_case.execute(
            user_id=user.id,
            first_name=user.first_name,
            lang=lang,
            username=user.username
        )

        # Confirmamos la acción al usuario
        confirm_text = (
            "✅ **Language set to English!**\n\nYou can now add me to your groups."
            if lang == "en" else
            "✅ **¡Idioma configurado en Español!**\n\nYa puedes añadirme a tus grupos."
        )

        await query.answer("Success! / ¡Logrado!")
        await query.edit_message_text(text=confirm_text, parse_mode="Markdown")

        logger.info(f"User {user.id} set language preference to {lang}")