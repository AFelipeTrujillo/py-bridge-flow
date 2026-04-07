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
        query = update.callback_query
        user = update.effective_user
        bot_username = context.bot.username
        _, lang = query.data.split("_")

        await self.update_user_use_case.execute(
            user_id=user.id, first_name=user.first_name, lang=lang, username=user.username
        )

        if lang == "es":
            confirm_text = (
                f"✅ **¡Idioma configurado!**\n\n"
                f"Sigue estos pasos para activar el bot en tu grupo:\n\n"
                f"1️⃣ Toca este nombre para copiarlo: `@{bot_username}`\n"
                f"2️⃣ Ve a tu grupo > **Añadir miembros** > Pega el nombre.\n"
                f"3️⃣ Una vez dentro, entra en el perfil del bot y selecciona **'Hacer administrador'**.\n"
                f"4️⃣ Asegúrate de activar el permiso: **'Invitar usuarios vía enlace'**."
            )
            btn_verify = "Comprobar estado 🔄"
        else:
            confirm_text = (
                f"✅ **Language set!**\n\n"
                f"Follow these steps to activate the bot:\n\n"
                f"1️⃣ Tap to copy: `@{bot_username}`\n"
                f"2️⃣ Go to your group > **Add Members** > Paste the name.\n"
                f"3️⃣ Tap the bot's profile and select **'Make Admin'**.\n"
                f"4️⃣ Enable the permission: **'Invite Users via Link'**."
            )
            btn_verify = "Check status 🔄"

        keyboard = [[InlineKeyboardButton(btn_verify, callback_data="check_admin_status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.answer()
        await query.edit_message_text(text=confirm_text, reply_markup=reply_markup, parse_mode="Markdown")