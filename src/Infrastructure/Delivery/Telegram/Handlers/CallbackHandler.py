import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ChatMemberHandler
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest

logger = logging.getLogger(__name__)

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
        """Procesa la selección de aprobación de administrador y finaliza el registro."""
        query = update.callback_query
        await query.answer()

        # 1. Parsear los datos del callback (formato: appr_yes_CHATID o appr_no_CHATID)
        try:
            parts = query.data.split("_")
            approval_required = parts[1] == "yes"
            chat_id = int(parts[2])
        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing callback data: {query.data} - {e}")
            await query.edit_message_text("❌ Error processing selection.")
            return

        # 2. Recuperar los datos temporales guardados en el RegistrationHandler
        registration_data = context.user_data.get(f"reg_{chat_id}")

        if not registration_data:
            error_msg = (
                "❌ **Session expired.**\n\nPlease remove and add the bot again to the group."
            )
            await query.edit_message_text(text=error_msg, parse_mode="Markdown")
            return

        # 3. Preparar el DTO para el Caso de Uso
        # Usamos los datos que heredamos del perfil del usuario (idioma) y del chat
        request_dto = RegisterGroupRequest(
            chat_id=registration_data["chat_id"],
            title=registration_data["title"],
            owner_id=registration_data["owner_id"],
            invite_link=registration_data.get("invite_link"),  # Opcional si ya lo tienes
            require_approval=approval_required,
            member_count=registration_data["member_count"],
            language=registration_data["language"]
        )

        try:
            # 4. Ejecutar el Caso de Uso (Guardar en MongoDB)
            await self.use_case.execute(request_dto)

            # 5. Seleccionar mensaje de éxito según el idioma guardado
            lang = registration_data["language"]

            if lang == "es":
                success_msg = (
                    "✅ **¡Registro completado!**\n\n"
                    f"El grupo **{registration_data['title']}** ahora forma parte de la red de difusión diaria.\n\n"
                    "No necesitas hacer nada más, yo me encargo del resto. 🚀"
                )
            else:
                success_msg = (
                    "✅ **Registration complete!**\n\n"
                    f"Group **{registration_data['title']}** is now part of the daily broadcast network.\n\n"
                    "You're all set, I'll handle the rest! 🚀"
                )

            # 6. Actualizar el mensaje en el chat privado del admin
            await query.edit_message_text(text=success_msg, parse_mode="Markdown")

            logger.info(f"Group {chat_id} successfully registered by user {registration_data['owner_id']}")

        except Exception as e:
            logger.error(f"Failed to register group {chat_id}: {e}")
            await query.edit_message_text("❌ An error occurred while saving the group.")

        finally:
            # 7. Limpiar la memoria temporal para evitar saturar el context.user_data
            if f"reg_{chat_id}" in context.user_data:
                del context.user_data[f"reg_{chat_id}"]