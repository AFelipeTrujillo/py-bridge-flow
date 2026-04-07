from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest


class RegistrationHandler:
    def __init__(self, register_group_use_case: RegisterGroup):
        self.use_case = register_group_use_case

    async def on_bot_added_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detects when the bot is added to a new group and contacts the owner."""
        result = update.my_chat_member
        if result.new_chat_member.status in ["administrator"]:
            chat = result.chat
            user = update.effective_user  # The person who added the bot

            # Store temporary data in user_data to use after the callback
            context.user_data[f"reg_{chat.id}"] = {
                "chat_id": chat.id,
                "title": chat.title,
                "owner_id": user.id,
                "member_count": await chat.get_member_count()
            }

            # Send a Private Message to the admin
            keyboard = [
                [
                    InlineKeyboardButton("English 🇺🇸", callback_data=f"lang_en_{chat.id}"),
                    InlineKeyboardButton("Español 🇪🇸", callback_data=f"lang_es_{chat.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=user.id,
                text=f"Hello! Thanks for adding me to **{chat.title}**.\n\n"
                     f"Please select the language for the daily broadcasts in this group:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )