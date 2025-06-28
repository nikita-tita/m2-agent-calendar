"""
Обработчики команд и сообщений
"""

from .text import router as text_router
from .voice import router as voice_router
from .photo import router as photo_router
from .admin import router as admin_router
from .calendar import router as calendar_router
from .analytics import router as analytics_router

__all__ = [
    "text_router",
    "voice_router", 
    "photo_router",
    "admin_router",
    "calendar_router",
    "analytics_router"
] 