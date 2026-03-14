"""
Конфигурация бота — читает из .env файла
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Обязательные
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Твой Telegram chat_id для авто-отчётов
    # Узнай его: напиши @userinfobot в Telegram
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Как часто делать авто-анализ (в часах)
    AUTO_ANALYZE_HOURS: int = int(os.getenv("AUTO_ANALYZE_HOURS", "6"))

    # Прокси (опционально, если Etsy блокирует)
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
