import logging
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Args:
            rate_limit: Минимальный интервал между запросами в секундах
        """
        self.rate_limit = rate_limit
        self.last_request_time: Dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем telegram_id из события
        if isinstance(event, (Message, CallbackQuery)):
            telegram_id = event.from_user.id
        else:
            # Для других типов событий пропускаем
            return await handler(event, data)
        
        current_time = time.time()
        last_time = self.last_request_time.get(telegram_id, 0)
        
        # Проверяем, не слишком ли часто пользователь отправляет запросы
        if current_time - last_time < self.rate_limit:
            logger.warning(f"User {telegram_id} is sending requests too frequently")
            
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Слишком много запросов. Подождите немного."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Слишком много запросов. Подождите немного.",
                    show_alert=True
                )
            return
        
        # Обновляем время последнего запроса
        self.last_request_time[telegram_id] = current_time
        
        # Вызываем следующий обработчик
        return await handler(event, data) 