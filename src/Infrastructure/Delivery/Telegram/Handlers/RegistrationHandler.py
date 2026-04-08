import logging
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class RegistrationHandler:
    def __init__(self, register_group_use_case, user_repo):
        self.register_group_use_case = register_group_use_case
        self.user_repo = user_repo

    async def on_bot_added_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detecta cuando el bot es añadido o cambia de estatus en un chat/canal."""
        result = update.my_chat_member
        chat = result.chat
        new_status = result.new_chat_member
        user_who_added = result.from_user

        # 1. Filtrar solo cuando el bot sea nombrado Administrador
        if new_status.status != ChatMember.ADMINISTRATOR:
            return

        # 2. Recuperar idioma del usuario (dueño)
        user_lang = await self._get_user_lang(user_who_added.id)

        # 3. Verificación CRÍTICA de permisos (funciona en Grupos y Canales)
        # Usamos getattr por seguridad si el objeto no tiene el atributo
        can_invite = getattr(new_status, "can_invite_users", False)

        if not can_invite:
            error_text = (
                f"⚠️ **¡Casi listo en {chat.title}!**\n\n"
                "Me has hecho admin, pero me falta el permiso de **'Invitar usuarios vía enlace'** (Invite Users via Link).\n"
                "Por favor, actívalo y pulsa el botón de abajo."
                if user_lang == "es" else
                f"⚠️ **Almost ready in {chat.title}!**\n\n"
                "I'm an admin, but I need the **'Invite Users via Link'** permission.\n"
                "Please enable it and tap the button below."
            )
            keyboard = [[InlineKeyboardButton("Reintentar / Retry 🔄", callback_data="check_admin_status")]]
            await context.bot.send_message(
                chat_id=user_who_added.id,
                text=error_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        else:
            try:
                link_obj = await chat.create_invite_link(name="Broadcast Bot Link")
                invite_link = link_obj.invite_link
            except Exception as e:
                logger.warning(f"No se pudo exportar el link, intentando crear uno: {e}")
                return

        try:
            current_count = await context.bot.get_chat_member_count(chat.id)
        except Exception:
            current_count = 0

        # 4. Almacenar datos temporales para el paso final (Aprobación)
        # Guardamos el tipo de chat (channel/group/supergroup)
        context.user_data[f"reg_{chat.id}"] = {
            "chat_id": chat.id,
            "title": chat.title,
            "owner_id": user_who_added.id,
            "language": user_lang,
            "member_count": current_count,
            "chat_type": chat.type,
            "invite_link": invite_link
        }

        # 5. Configuración de idioma para la pregunta de aprobación
        if user_lang == "es":
            msg = f"✅ ¡Detectado correctamente en **{chat.title}**!\n\n¿Los nuevos miembros requieren aprobación de un administrador?"
            btns = [
                InlineKeyboardButton("Sí", callback_data=f"appr_yes_{chat.id}"),
                InlineKeyboardButton("No", callback_data=f"appr_no_{chat.id}")
            ]
        else:
            msg = f"✅ Successfully detected in **{chat.title}**!\n\nShould new members require admin approval?"
            btns = [
                InlineKeyboardButton("Yes", callback_data=f"appr_yes_{chat.id}"),
                InlineKeyboardButton("No", callback_data=f"appr_no_{chat.id}")
            ]

        await context.bot.send_message(
            chat_id=user_who_added.id,
            text=msg,
            reply_markup=InlineKeyboardMarkup([btns]),
            parse_mode="Markdown"
        )

        logger.info(f"Bot set as admin in {chat.type} {chat.title} ({chat.id}) by {user_who_added.id}")

    async def _get_user_lang(self, user_id: int) -> str:
        """Helper para obtener el idioma del usuario desde el repositorio."""
        try:
            user = await self.user_repo.find_by_id(user_id)
            if user:
                return user.language
        except Exception as e:
            logger.error(f"Error fetching user lang: {e}")
        return "en"