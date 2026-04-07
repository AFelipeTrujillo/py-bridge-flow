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

            # 1. Recuperamos el idioma del usuario desde el repositorio
            existing_user = await self.user_repo.find_by_id(user_who_added.id)
            user_lang = existing_user.language if existing_user else "en"

            # 2. Definimos los mensajes según el idioma
            if user_lang == "es":
                msg_intro = f"Configurando **{chat.title}**... ⚙️"
                msg_question = "¿Los nuevos miembros requieren aprobación de un administrador?"
                btn_yes = "Sí"
                btn_no = "No"
            else:
                msg_intro = f"Configuring **{chat.title}**... ⚙️"
                msg_question = "Should new members require admin approval?"
                btn_yes = "Yes"
                btn_no = "No"

            # 3. Guardamos los datos temporales en context.user_data
            context.user_data[f"reg_{chat.id}"] = {
                "chat_id": chat.id,
                "title": chat.title,
                "owner_id": user_who_added.id,
                "language": user_lang,
                "member_count": await chat.get_member_count()
            }

            # 4. Creamos el teclado con los textos traducidos
            keyboard = [
                [
                    InlineKeyboardButton(btn_yes, callback_data=f"appr_yes_{chat.id}"),
                    InlineKeyboardButton(btn_no, callback_data=f"appr_no_{chat.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # 5. Enviamos el mensaje al ADMIN (en privado)
            await context.bot.send_message(
                chat_id=user_who_added.id,
                text=f"{msg_intro}\n\n{msg_question}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )