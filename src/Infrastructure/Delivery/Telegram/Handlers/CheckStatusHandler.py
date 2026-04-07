from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.Domain.Repository.GroupRepository import GroupRepository


class CheckStatusHandler:
    def __init__(self, group_repo: GroupRepository):
        self.group_repo = group_repo

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        query = update.callback_query

        if query:
            await query.answer()

        # Lógica de búsqueda
        groups = await self.group_repo.find_by_owner(user_id)

        # 1. Recuperar el idioma (opcional, pero recomendado)
        # Si tienes el user_repo inyectado, podrías usar _get_user_lang aquí también
        lang = "es"  # Por ahora lo dejamos en ES, o recupéralo de la sesión

        # 2. Preparar el botón de reintento
        btn_text = "Reintentar comprobación 🔄" if lang == "es" else "Retry check 🔄"
        keyboard = [[InlineKeyboardButton(btn_text, callback_data="check_admin_status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if not groups:
            text = (
                "❌ **No he detectado grupos bajo tu propiedad.**\n\n"
                "Esto puede deberse a:\n"
                "1️⃣ No me has añadido a ningún grupo.\n"
                "2️⃣ Me añadiste pero **no me diste permisos de Administrador**.\n"
                "3️⃣ Me diste permisos pero olvidaste el de **'Invitar usuarios vía enlace'**.\n\n"
                "💡 *Una vez corregido, pulsa el botón de abajo:*"
            )
        else:
            report = "📋 **Estado de tus grupos:**\n\n"
            for g in groups:
                status = "✅ Activo" if g.is_active else "⚠️ Pendiente"
                report += f"• **{g.title}**: {status}\n"
            text = report

        # 3. Enviar respuesta con el teclado
        if query:
            try:
                await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
            except Exception:
                # Si falla por ser el mismo texto, ignoramos para no ensuciar el log
                pass
        else:
            await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")