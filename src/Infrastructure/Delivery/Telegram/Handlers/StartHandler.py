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
        await query.answer()

        lang = query.data.split("_")[1]
        user_id = update.effective_user.id
        telegram_user = update.effective_user
        first_name = telegram_user.first_name
        username = telegram_user.username

        await self.update_user_use_case.execute(
            user_id = user_id,
            first_name = first_name,
            lang = lang,
            username = username
        )

        context.user_data["lang"] = lang

        await self._show_main_menu(query, lang)


    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_lang = context.user_data.get("lang", "en")  # O recuperado de DB

        if user_lang == "es":
            text = "👋 **¡Bienvenido a la Red!**\n\n¿Qué te gustaría hacer hoy?"
            buttons = [
                [InlineKeyboardButton("🔍 Explorar Grupos", callback_data="explore_groups")],
                [InlineKeyboardButton("🚀 Registrar mi Grupo/Canal", callback_data="start_registration")]
            ]
        else:
            text = "👋 **Welcome to the Network!**\n\nWhat would you like to do today?"
            buttons = [
                [InlineKeyboardButton("🔍 Explore Groups", callback_data="explore_groups")],
                [InlineKeyboardButton("🚀 Register my Group/Channel", callback_data="start_registration")]
            ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

    async def _show_main_menu(self, query, lang: str):
        if lang == "es":
            text = "👋 **Menú Principal**\n\n¿Qué deseas hacer?"
            btn_explore = "🔍 Explorar Grupos"
            btn_register = "🚀 Registrar mi Grupo"
        else:
            text = "👋 **Main Menu**\n\nWhat would you like to do?"
            btn_explore = "🔍 Explore Groups"
            btn_register = "🚀 Register my Group"

        keyboard = [
            [InlineKeyboardButton(btn_explore, callback_data="main_explore")],
            [InlineKeyboardButton(btn_register, callback_data="main_register")]
        ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )