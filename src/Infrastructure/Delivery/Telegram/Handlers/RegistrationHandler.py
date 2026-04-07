from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler
from src.Domain.Repository.UserRepository import UserRepository
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest


class RegistrationHandler:
    def __init__(self, register_group_use_case: RegisterGroup, user_repo: UserRepository):
        self.use_case = register_group_use_case
        self.user_repo = user_repo

    async def on_bot_added_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = update.my_chat_member
        if result.new_chat_member.status == "administrator":
            chat = result.chat
            user_who_added = update.effective_user

            # 1. Check if we already know this user's language
            existing_user = await self.user_repo.find_by_id(user_who_added.id)
            user_lang = existing_user.language if existing_user else "en"

            # 2. Store session data
            context.user_data[f"reg_{chat.id}"] = {
                "chat_id": chat.id,
                "title": chat.title,
                "owner_id": user_who_added.id,
                "language": user_lang,  # Inherited from user profile!
                "member_count": await chat.get_member_count()
            }

            # 3. Send message in their language
            msg = (
                f"Configuring **{chat.title}**..." if user_lang == "en"
                else f"Configurando **{chat.title}**..."
            )

            # Ask for Join Request setting (the only thing left to know)
            keyboard = [
                [
                    InlineKeyboardButton("Yes/Sí", callback_data=f"appr_yes_{chat.id}"),
                    InlineKeyboardButton("No", callback_data=f"appr_no_{chat.id}")
                ]
            ]

            await context.bot.send_message(
                chat_id=user_who_added.id,
                text=f"{msg}\n\nShould new members require admin approval?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )