import asyncio
import logging
import os
import certifi
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder, ChatMemberHandler, CallbackQueryHandler
from telegram.ext import ChatJoinRequestHandler, CommandHandler
from motor.motor_asyncio import AsyncIOMotorClient

from src.Application.UseCase.UpdateUserPreference import UpdateUserPreference
# Persistence
from src.Infrastructure.Persistence.MongoGroupRepository import MongoGroupRepository
from src.Infrastructure.Persistence.MongoUserRepository import MongoUserRepository
from src.Infrastructure.Persistence.MongoClient import get_database
from src.Infrastructure.Config.Settings import settings
from src.Infrastructure.Delivery.Telegram.Jobs.BroadcastJob import BroadcastJob

# Use Cases
from src.Application.UseCase.RegisterGroup import RegisterGroup
from src.Application.UseCase.DailyBroadcast import DailyBroadcast
from src.Application.UseCase.GetSystemStatus import GetSystemStatus
from src.Application.UseCase.GetWelcomeMessage import GetWelcomeMessage

# Handlers
from src.Infrastructure.Delivery.Telegram.Handlers.RegistrationHandler import RegistrationHandler
from src.Infrastructure.Delivery.Telegram.Handlers.CallbackHandler import CallbackHandler
from src.Infrastructure.Delivery.Telegram.Handlers.MemberHandler import MemberHandler
from src.Infrastructure.Delivery.Telegram.Handlers.StatusHandler import StatusHandler
from src.Infrastructure.Delivery.Telegram.Handlers.StartHandler import StartHandler
from src.Infrastructure.Delivery.Telegram.Handlers.CheckStatusHandler import CheckStatusHandler



# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env


def main():
    # 1. Database Initialization
    client  = AsyncIOMotorClient(settings.MONGO_URI, tlsCAFile=certifi.where())
    db      = get_database(client, settings.DB_NAME)

    # 2. Dependency Injection
    group_repo  = MongoGroupRepository(db)
    user_repo   = MongoUserRepository(db)

    # Instantiate Use Cases
    register_use_case       = RegisterGroup(group_repo)
    broadcast_use_case      = DailyBroadcast(group_repo)
    status_use_case         = GetSystemStatus(group_repo)
    welcome_use_case        = GetWelcomeMessage()
    update_user_use_case    = UpdateUserPreference(user_repo)

    # Instantiate Handlers (Delivery Layer)
    member_logic        = MemberHandler(group_repo)
    reg_handler_logic   = RegistrationHandler(register_use_case, user_repo)
    callback_logic      = CallbackHandler(register_use_case, user_repo, group_repo, settings.SUPER_ADMIN_ID)
    broadcast_job_logic = BroadcastJob(broadcast_use_case)
    status_logic        = StatusHandler(status_use_case)
    start_logic         = StartHandler(welcome_use_case, update_user_use_case)
    check_status_logic  = CheckStatusHandler(group_repo)

    # 3. Bot Initialization
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(ChatMemberHandler(
        reg_handler_logic.on_bot_added_to_group,
        chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER
    ))
    application.add_handler(CallbackQueryHandler(start_logic.handle_callback, pattern=r"^setlang_"))
    application.add_handler(ChatJoinRequestHandler(member_logic.on_join_request))
    application.add_handler(CommandHandler("status", status_logic.handle))
    application.add_handler(CommandHandler("start", start_logic.handle))
    application.add_handler(CommandHandler("check", check_status_logic.handle))
    application.add_handler(CallbackQueryHandler(check_status_logic.handle, pattern=r"^check_admin_status$"))

    # 4. Register Telegram Handlers
    # Handle when bot is added to a group
    application.add_handler(ChatMemberHandler(
        reg_handler_logic.on_bot_added_to_group,
        ChatMemberHandler.MY_CHAT_MEMBER
    ))

    # 5. Initialize the Scheduler
    if application.job_queue:
        broadcast_job_logic.schedule(
            application.job_queue,
            settings.BROADCAST_TIME_UTC
        )
    else:
        logger.warning("JobQueue is not available. Daily broadcasts will not run.")

    # Handle Language selection buttons
    application.add_handler(CallbackQueryHandler(
        callback_logic.handle_language_selection,
        pattern=r"^lang_"
    ))

    # Handle Approval selection buttons
    application.add_handler(CallbackQueryHandler(
        callback_logic.handle_user_approval_selection,
        pattern=r"^appr_"
    ))

    application.add_handler(CallbackQueryHandler(
        callback_logic.handle_admin_moderation,
        pattern=r"^admin_"
    ))

    """

    # 2. Maneja la moderación del ADMIN (Ej: admin_appr_123)
    application.add_handler(CallbackQueryHandler(
        callback_logic.handle_admin_moderation,
        pattern=r"^admin_"
    ))

    # 3. El botón de comprobación de estado
    application.add_handler(CallbackQueryHandler(
        check_status_logic.handle,
        pattern=r"^check_admin_status$"
    ))

    # 4. Selección de idioma inicial (si usas 'lang_')
    application.add_handler(CallbackQueryHandler(
        callback_logic.handle_language_selection,
        pattern=r"^lang_"
    ))
"""
    # 6. Start the Bot
    logger.info("Bot started and listening for updates...")
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")