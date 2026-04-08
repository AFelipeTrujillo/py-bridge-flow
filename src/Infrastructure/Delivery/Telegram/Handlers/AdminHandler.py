import logging
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.Application.UseCase.DailyBroadcast import DailyBroadcast
from src.Domain.Repository.GroupRepository import GroupRepository

logger = logging.getLogger(__name__)


class AdminHandler:
    def __init__(self, broadcast_use_case: DailyBroadcast, group_repo: GroupRepository, admin_id: int):
        self.use_case = broadcast_use_case
        self.group_repo = group_repo
        self.admin_id = admin_id

    async def force_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /force_broadcast para probar el envío masivo."""
        if update.effective_user.id != self.admin_id:
            return  # Solo el admin puede ejecutarlo

        await update.message.reply_text("🚀 Iniciando broadcast de prueba...")

        # --- MISMA LÓGICA QUE EL JOB ---
        targets = await self.group_repo.get_all_active()
        msg_es = await self.use_case.execute(lang="es")
        msg_en = await self.use_case.execute(lang="en")

        bot_username = (await context.bot.get_me()).username
        start_url = f"https://t.me/{bot_username}?start=setup"

        btn_es = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Registra tu grupo", url=start_url)
        ]])

        btn_en = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Register your group", url=start_url)
        ]])

        for target in targets:
            if target.language == "es":
                text = msg_es
                reply_markup = btn_es
            else:
                text = msg_en
                reply_markup = btn_en

            try:
                await context.bot.send_message(
                    chat_id=target.chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Error enviando broadcast: {e}")

        await update.message.reply_text("✅ Broadcast completado.")