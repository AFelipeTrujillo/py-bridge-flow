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
        """Revisa si el grupo existe en cada mensaje recibido."""
        if not update.effective_chat or update.effective_chat.type == "private":
            return

        chat = update.effective_chat

        # 1. Buscar en la base de datos
        exists = await self.repo.find_by_id(chat.id)

        if not exists:
            logger.info(f"🔍 Detectado grupo 'fantasma': {chat.title} ({chat.id})")

            try:
                # 2. Intentar obtener datos básicos
                count = await context.bot.get_chat_member_count(chat.id)

                # Intentamos obtener el link si el bot es admin
                invite_link = chat.invite_link or "Pending/Unknown"

                request = RegisterGroupRequest(
                    chat_id=chat.id,
                    title=chat.title,
                    owner_id=0,
                    invite_link=invite_link,
                    chat_type=chat.type,
                    member_count=count,
                    language="es"
                )

                await self.register_use_case.execute(request)
                logger.info(f"✅ Grupo {chat.title} auto-registrado.")

                # 3. NOTIFICACIÓN AL DUEÑO DEL BOT
                notification_text = (
                    "🕵️‍♂️ **Nuevo Grupo Detectado Automáticamente**\n\n"
                    f"🏷 **Título:** {chat.title}\n"
                    f"🆔 **ID:** `{chat.id}`\n"
                    f"👥 **Miembros:** {count}\n"
                    f"type **Tipo:** {chat.type}\n"
                    f"🔗 **Link:** {invite_link}\n\n"
                    "⚠️ _El grupo ha sido registrado con estado 'pending' y owner_id 0._"
                )

                await context.bot.send_message(
                    chat_id=self.admin_id,
                    text=notification_text,
                    parse_mode="Markdown"
                )

            except Exception as e:
                logger.error(f"❌ Falló el auto-registro de {chat.id}: {e}")