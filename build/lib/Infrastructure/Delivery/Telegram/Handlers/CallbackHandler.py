from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest

class CallbackHandler:
    def __init__(self, register_group_use_case: RegisterGroup):
        self.use_case = register_group_use_case

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # Data format: lang_{lang}_{chat_id}
        _, lang, chat_id = query.data.split("_")
        context.user_data[f"reg_{chat_id}"]["language"] = lang

        keyboard = [
            [
                InlineKeyboardButton("Yes (Manual Approval)", callback_data=f"appr_yes_{chat_id}"),
                InlineKeyboardButton("No (Direct Join)", callback_data=f"appr_no_{chat_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="Got it! Now, should new members via the bot link require admin approval to join?",
            reply_markup=reply_markup
        )

    async def handle_approval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        _, choice, chat_id = query.data.split("_")
        data = context.user_data.get(f"reg_{chat_id}")

        require_approval = True if choice == "yes" else False

        # 1. Create the Invite Link via Telegram API
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=int(chat_id),
            creates_join_request=require_approval
        )

        # 2. Prepare the DTO for the Use Case
        request_dto = RegisterGroupRequest(
            chat_id=data["chat_id"],
            title=data["title"],
            owner_id=data["owner_id"],
            invite_link=invite_link_obj.invite_link,
            require_approval=require_approval,
            member_count=data["member_count"],
            language=data["language"]
        )

        # 3. Execute the Use Case
        await self.use_case.execute(request_dto)

        await query.edit_message_text(
            text="✅ Registration complete! Your group is now part of the daily broadcast network."
        )
        # Clean up temp data
        del context.user_data[f"reg_{chat_id}"]