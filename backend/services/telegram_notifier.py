"""
Authoritative compatibility wrapper for telegram_service.
Unifies all imports to backend.services.telegram_service.
"""
from backend.services.telegram_service import (
    TelegramService,
    TelegramNotifierService,
    telegram_service,
)

__all__ = ["TelegramService", "TelegramNotifierService", "telegram_service"]
