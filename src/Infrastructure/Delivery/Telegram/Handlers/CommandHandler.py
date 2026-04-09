import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, register_group_use_case: RegisterGroup):
        self.register_use_case = register_group_use_case

    async def sync_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forzar el registro de un grupo donde el bot ya es admin."""
        chat = update.effective_chat
        user = update.effective_user

        if chat.type == "private":
            await update.message.reply_text("❌ Este comando solo funciona dentro de grupos o canales.")
            return

        # Verificar si el usuario es admin para evitar registros basura
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ["creator", "administrator"]:
            return  # Silencioso o mensaje de error

        try:
            # Intentar obtener datos reales de Telegram
            member_count = await context.bot.get_chat_member_count(chat.id)

            # Intentar obtener o generar el link
            invite_link = chat.invite_link
            if not invite_link:
                # Si no tiene link, intentamos exportar uno nuevo
                invite_link = await context.bot.export_chat_invite_link(chat.id)

            request = RegisterGroupRequest(
                chat_id=chat.id,
                title=chat.title,
                owner_id=user.id,
                invite_link=invite_link,
                chat_type=chat.type,
                member_count=member_count,
                language=context.user_data.get("lang", "es")
            )

            await self.register_use_case.execute(request)

            await update.message.reply_text(
                f"✅ **Grupo Sincronizado**\n\n"
                f"El bot ha detectado correctamente a '{chat.title}' y lo ha indexado en la base de datos."
            )

        except Exception as e:
            logger.error(f"Error sincronizando grupo {chat.id}: {e}")
            await update.message.reply_text(
                "❌ No pude sincronizar el grupo. Asegúrate de que soy Administrador con permisos de invitación.")