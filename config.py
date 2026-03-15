import os

class Config:
    TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_TOKEN", "")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")
    AUTO_ANALYZE_HOURS: int = int(os.environ.get("AUTO_ANALYZE_HOURS", "6"))
