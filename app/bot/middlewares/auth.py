import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации пользователей"""
    
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
        
        # Получаем сессию БД
        async for session in get_async_session():
            try:
                # Ищем пользователя в базе
                result = await session.execute(
                    text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
                    {"telegram_id": telegram_id}
                )
                user_data = result.fetchone()
                
                if user_data:
                    # Пользователь найден, создаем объект User
                    user = User(
                        id=user_data.id,
                        telegram_id=user_data.telegram_id,
                        username=user_data.username,
                        first_name=user_data.first_name,
                        last_name=user_data.last_name,
                        phone=user_data.phone,
                        timezone=user_data.timezone,
                        settings=user_data.settings or {},
                        is_active=user_data.is_active,
                        is_admin=user_data.is_admin,
                        created_at=user_data.created_at,
                        updated_at=user_data.updated_at
                    )
                    
                    # Проверяем активность пользователя
                    if not user.is_active:
                        if isinstance(event, Message):
                            await event.answer(
                                "❌ Ваш аккаунт заблокирован. Обратитесь к администратору."
                            )
                        elif isinstance(event, CallbackQuery):
                            await event.answer(
                                "❌ Ваш аккаунт заблокирован. Обратитесь к администратору.",
                                show_alert=True
                            )
                        return
                    
                    # Добавляем пользователя в контекст
                    data["user"] = user
                    data["session"] = session
                    
                    # Обновляем информацию о пользователе если нужно
                    if isinstance(event, Message):
                        await self._update_user_info(event, user, session)
                    
                else:
                    # Пользователь не найден, создаем нового
                    user = await self._create_user(event, session)
                    if user:
                        data["user"] = user
                        data["session"] = session
                    else:
                        # Ошибка создания пользователя
                        if isinstance(event, Message):
                            await event.answer(
                                "❌ Ошибка регистрации. Попробуйте команду /start"
                            )
                        return
                
                # Вызываем следующий обработчик
                return await handler(event, data)
                
            except Exception as e:
                logger.error(f"Error in AuthMiddleware: {e}")
                # В случае ошибки пропускаем middleware
                return await handler(event, data)
    
    async def _update_user_info(self, message: Message, user: User, session: AsyncSession) -> None:
        """Обновляет информацию о пользователе"""
        try:
            # Проверяем, изменилась ли информация
            if (user.username != message.from_user.username or 
                user.first_name != message.from_user.first_name or 
                user.last_name != message.from_user.last_name):
                
                await session.execute(
                    text("""
                    UPDATE users 
                    SET username = :username, first_name = :first_name, last_name = :last_name, updated_at = NOW()
                    WHERE telegram_id = :telegram_id
                    """),
                    {
                        "telegram_id": user.telegram_id,
                        "username": message.from_user.username,
                        "first_name": message.from_user.first_name,
                        "last_name": message.from_user.last_name
                    }
                )
                await session.commit()
                
                # Обновляем объект пользователя
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                
        except Exception as e:
            logger.error(f"Error updating user info: {e}")
    
    async def _create_user(self, event: TelegramObject, session: AsyncSession) -> User | None:
        """Создает нового пользователя"""
        try:
            if isinstance(event, (Message, CallbackQuery)):
                telegram_id = event.from_user.id
                username = event.from_user.username
                first_name = event.from_user.first_name
                last_name = event.from_user.last_name
            else:
                return None
            
            # Создаем пользователя
            await session.execute(
                text("""
                INSERT INTO users (telegram_id, username, first_name, last_name, timezone, settings, is_active, is_admin, is_verified, enable_notifications, notification_language, created_at, updated_at)
                VALUES (:telegram_id, :username, :first_name, :last_name, :timezone, :settings, :is_active, :is_admin, :is_verified, :enable_notifications, :notification_language, NOW(), NOW())
                """),
                {
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "timezone": "Europe/Moscow",
                    "settings": "{}",
                    "is_active": True,
                    "is_admin": False,
                    "is_verified": False,
                    "enable_notifications": True,
                    "notification_language": "ru"
                }
            )
            await session.commit()
            
            # Получаем созданного пользователя
            result = await session.execute(
                text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_id}
            )
            user_data = result.fetchone()
            
            if user_data:
                user = User(
                    id=user_data.id,
                    telegram_id=user_data.telegram_id,
                    username=user_data.username,
                    first_name=user_data.first_name,
                    last_name=user_data.last_name,
                    phone=user_data.phone,
                    timezone=user_data.timezone,
                    settings=user_data.settings or {},
                    is_active=user_data.is_active,
                    is_admin=user_data.is_admin,
                    created_at=user_data.created_at,
                    updated_at=user_data.updated_at
                )
                
                logger.info(f"Created new user: {user.telegram_id}")
                return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        
        return None 