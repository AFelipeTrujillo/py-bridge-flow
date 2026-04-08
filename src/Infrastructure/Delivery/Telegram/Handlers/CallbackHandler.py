import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest

logger = logging.getLogger(__name__)

class CallbackHandler:
    def __init__(self, register_group_use_case: RegisterGroup, user_repo, group_repo, super_admin_id: int):
        self.register_group_use_case = register_group_use_case
        self.user_repo = user_repo
        self.super_admin_id = super_admin_id
        self.group_repo = group_repo


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

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Punto de entrada principal para todos los callbacks."""
        query = update.callback_query
        data = query.data

        if data.startswith("appr_"):
            await self.handle_user_approval_selection(update, context)
        elif data.startswith("admin_"):
            await self.handle_admin_moderation(update, context)

    async def handle_user_approval_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """El usuario finaliza la configuración de su grupo."""
        query = update.callback_query
        await query.answer()

        parts = query.data.split("_")
        approval_required = parts[1] == "yes"
        chat_id = int(parts[2])

        registration_data = context.user_data.get(f"reg_{chat_id}")
        if not registration_data:
            await query.edit_message_text("❌ Error: Session expired. Try adding the bot again.")
            return

        # 1. Guardar el grupo con estado 'pending'
        request_dto = RegisterGroupRequest(
            chat_id=registration_data["chat_id"],
            title=registration_data["title"],
            owner_id=registration_data["owner_id"],
            invite_link=registration_data["invite_link"],
            require_approval=approval_required,
            member_count=registration_data["member_count"],
            language=registration_data["language"],
            chat_type=registration_data["chat_type"],
            status="pending"
        )

        try:
            await self.register_group_use_case.execute(request_dto)

            # 2. Confirmación al Usuario
            lang = registration_data["language"]
            user_msg = (
                "📩 **Solicitud enviada con éxito.**\n\n"
                "Un administrador revisará tu grupo/canal pronto para validar que cumpla con las normas.\n"
                "Te avisaremos por aquí una vez sea aprobado. ¡Gracias!"
                if lang == "es" else
                "📩 **Request sent successfully.**\n\n"
                "An administrator will review your group/channel shortly to validate it.\n"
                "We'll notify you here once it's approved. Thanks!"
            )
            await query.edit_message_text(text=user_msg, parse_mode="Markdown")

            # 3. Notificación al Super-Admin (Tú)
            await self._notify_super_admin(update, context, registration_data)

        except Exception as e:
            logger.error(f"Error saving pending group: {e}")
            await query.edit_message_text("❌ Error saving request.")

    async def _notify_super_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
        """Envía una ficha de revisión al dueño del bot."""
        owner = update.effective_user
        chat_id = data["chat_id"]

        # Link para hablar con el dueño
        owner_contact = f"https://t.me/{owner.username}" if owner.username else f"tg://user?id={owner.id}"

        admin_report = (
            "🆕 **SOLICITUD DE REVISIÓN**\n\n"
            f"🏠 **Nombre:** {data['title']}\n"
            f"🏷 **Tipo:** {data['chat_type']}\n"
            f"👥 **Miembros:** {data['member_count']}\n"
            f"🔗 **Link:** {data['invite_link']}\n\n"
            f"👤 **Dueño:** {owner.first_name} (@{owner.username or 'N/A'})\n"
        )

        keyboard = [
            [InlineKeyboardButton("Hablar con dueño 💬", url=owner_contact)],
            [
                InlineKeyboardButton("Aprobar ✅", callback_data=f"admin_appr_{chat_id}"),
                InlineKeyboardButton("Rechazar ❌", callback_data=f"admin_reje_{chat_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=self.super_admin_id,
            text=admin_report,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_admin_moderation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Procesando moderación de administrador...")

        query = update.callback_query
        await query.answer()

        _, action_type, chat_id = query.data.split("_")
        chat_id = int(chat_id)

        is_approved = action_type == "appr"
        status = "approved" if is_approved else "rejected"

        try:
            await self.group_repo.update_status(chat_id, status)

            group_data = await self.group_repo.find_by_id(chat_id)
            if group_data:
                message = (
                    f"✅ Tu grupo **{group_data.title}** ha sido aprobado."
                    if is_approved
                    else f"❌ Tu solicitud para **{group_data.title}** fue rechazada."
                )
                await context.bot.send_message(
                    chat_id=group_data.owner_id,
                    text=message,
                    parse_mode="Markdown"
                )

            result_text = "✅ APROBADO" if is_approved else "❌ RECHAZADO"
            await query.edit_message_text(
                text=f"{query.message.text}\n\n**RESULTADO:** {result_text}",
                parse_mode="Markdown"
            )

            logger.info(f"Admin decidió: {status} para el chat {chat_id}")

        except Exception as e:
            logger.error(f"Error en handle_admin_moderation: {e}")
            await query.edit_message_text(
                text=f"❌ Error procesando moderación: {str(e)}"
            )