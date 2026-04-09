import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest

logger = logging.getLogger(__name__)


class AutoRegistrationHandler:
    def __init__(self, repository, register_use_case: RegisterGroup, admin_id: int):
        self.repo = repository
        self.register_use_case = register_use_case
        self.admin_id = admin_id  # Tu ID de Telegram

    async def check_and_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_chat or update.effective_chat.type == "private":
            return

        chat = update.effective_chat
        exists = await self.repo.find_by_id(chat.id)

        if not exists:
            logger.info(f"🔍 Detectado grupo 'fantasma': {chat.title} ({chat.id})")

            try:
                # 1. Obtener el conteo de miembros
                count = await context.bot.get_chat_member_count(chat.id)

                # 2. CORRECCIÓN: Intentar obtener el link de forma segura
                # Primero intentamos ver si el bot puede obtener el chat completo
                full_chat = await context.bot.get_chat(chat.id)
                invite_link = full_chat.invite_link

                # 3. Si sigue siendo None, intentamos exportar uno (requiere permiso de admin)
                if not invite_link:
                    try:
                        invite_link = await context.bot.export_chat_invite_link(chat.id)
                    except Exception:
                        invite_link = "Pending/Private"

                request = RegisterGroupRequest(
                    chat_id=chat.id,
                    title=chat.title,
                    owner_id=0,
                    invite_link=invite_link,
                    chat_type=chat.type,
                    member_count=count,
                    language="es",
                    require_approval=False
                )

                await self.register_use_case.execute(request)

                # Notificación al admin (ya corregida)
                notification_text = (
                    "🕵️‍♂️ **Nuevo Grupo Detectado**\n\n"
                    f"🏷 **Título:** {chat.title}\n"
                    f"🆔 **ID:** `{chat.id}`\n"
                    f"🔗 **Link:** {invite_link}"
                )
                await context.bot.send_message(chat_id=self.admin_id, text=notification_text, parse_mode="Markdown")

            except Exception as e:
                logger.error(f"❌ Falló el auto-registro de {chat.id}: {e}")