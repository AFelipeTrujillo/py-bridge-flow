import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.DTO.RegisterGroupRequest import RegisterGroupRequest
from src.Domain.Repository.GroupRepository import GroupRepository
from src.Domain.Repository.UserRepository import UserRepository

logger = logging.getLogger(__name__)

class CallbackHandler:
    def __init__(self, register_group_use_case: RegisterGroup, user_repo: UserRepository, group_repo: GroupRepository, super_admin_id: int):
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
        query = update.callback_query
        data = query.data

        if data == "main_explore":
            await self.handle_explore_groups(update, context)

        elif data == "main_register":
            await self.handle_show_registration_instructions(update, context)

        elif data == "main_menu":
            await self._show_main_menu(update, context)

        if data.startswith("appr_"):
            await self.handle_user_approval_selection(update, context)
        elif data.startswith("admin_"):
            await self.handle_admin_moderation(update, context)

    async def handle_show_registration_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        lang = context.user_data.get("lang", "en")

        bot_username = f"@{context.bot.username}"

        if lang == "es":
            text = (
                "🚀 **Cómo registrar tu grupo:**\n\n"
                f"1. Copia mi usuario: `{bot_username}` (toca para copiar).\n"
                "2. Añádeme como **Administrador** en tu grupo o canal.\n"
                "3. Asegúrate de darme el permiso de **'Invitar usuarios vía enlace'**.\n"
                "4. Una vez hecho, detectaré el grupo automáticamente y te enviaré aquí los pasos finales."
            )
            back_btn_text = "⬅️ Volver"
        else:
            text = (
                "🚀 **How to register your group:**\n\n"
                f"1. Copy my username: `{bot_username}` (tap to copy).\n"
                "2. Add me as an **Admin** in your group or channel.\n"
                "3. Make sure to grant the **'Invite users via link'** permission.\n"
                "4. Once done, I'll detect the group and send you the final steps here."
            )
            back_btn_text = "⬅️ Back"

        keyboard = [[InlineKeyboardButton(back_btn_text, callback_data="main_menu")]]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

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

    async def handle_explore_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        lang = context.user_data.get("lang", "en")
        approved_groups = await self.group_repo.find_all_approved()

        # Traducciones y Textos
        if lang == "es":
            empty_text = "😔 Por ahora no hay grupos aprobados. ¡Vuelve pronto!"
            header_text = "📂 **DIRECTORIO DE COMUNIDADES**\n_Toca el nombre para unirte_\n\n---\n"
            footer_text = "\n---\n**Simbología:** 📢 Canal | 👥 Grupo"
            back_btn_text = "⬅️ Volver"
        else:
            empty_text = "😔 No approved groups yet. Check back soon!"
            header_text = "📂 **COMMUNITY DIRECTORY**\n_Tap the name to join_\n\n---\n"
            footer_text = "\n---\n**Legend:** 📢 Channel | 👥 Group"
            back_btn_text = "⬅️ Back"

        keyboard = [[InlineKeyboardButton(back_btn_text, callback_data="main_menu")]]

        if not approved_groups:
            await query.edit_message_text(text=empty_text, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        report = header_text

        for g in approved_groups:
            # 1. Formatear el número de miembros
            members = self.format_member_count(g.member_count)

            # 2. Determinar el emoji según el tipo de chat
            # Asumimos que g.chat_type puede ser 'channel', 'supergroup' o 'group'
            icon = "📢" if g.chat_type == "channel" else "👥"

            # 3. Construir la línea: Emoji + [Nombre](Link) + Miembros + Icono Tipo
            # El uso de ` ` (code) ayuda a que los números se vean alineados
            report += f"🔹 [{g.title}]({g.invite_link})  `{members}`  {icon}\n"

        report += footer_text

        await query.edit_message_text(
            text=report,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            disable_web_page_preview=True  # Crucial para que no se llene de vistas previas
        )

    def format_member_count(self, count: int) -> str:
        if count < 1000:
            return str(count)
        if count < 10000:
            # Un decimal para miles bajos (ej: 1.3K)
            return f"+{count / 1000:.1f}K"
        # Sin decimales para números muy grandes (ej: +12K)
        return f"+{int(count / 1000)}K"

    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # Recuperamos el idioma guardado en el context
        lang = context.user_data.get("lang", "en")

        if lang == "es":
            text = "👋 **Menú Principal**\n\n¿Qué quieres hacer hoy?"
            btns = [
                [InlineKeyboardButton("🔍 Explorar Grupos", callback_data="main_explore")],
                [InlineKeyboardButton("🚀 Registrar mi Grupo", callback_data="main_register")]
            ]
        else:
            text = "👋 **Main Menu**\n\nWhat would you like to do today?"
            btns = [
                [InlineKeyboardButton("🔍 Explore Groups", callback_data="main_explore")],
                [InlineKeyboardButton("🚀 Register my Group", callback_data="main_register")]
            ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="Markdown"
        )