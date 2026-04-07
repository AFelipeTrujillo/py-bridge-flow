import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """System configuration and environment variables."""

    # Telegram Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")

    # MongoDB Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "telegram_bot_manager")

    # Broadcast Configuration
    # Defaulting to 12:00 PM if not specified
    BROADCAST_TIME_UTC: str = os.getenv("BROADCAST_TIME_UTC", "12:00")

    def __post_init__(self):
        """Validate that essential variables are present."""
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is missing in the environment variables.")

        if not self.MONGO_URI:
            raise ValueError("MONGO_URI is missing in the environment variables.")


# Singleton instance to be used across the app
settings = Settings()