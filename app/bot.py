"""
Основной файл Telegram бота
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import settings
from app.core.middleware import DatabaseMiddleware, UserMiddleware
from app.handlers import (
    text_router,
    voice_router,
    photo_router,
    admin_router,
    calendar_router,
    analytics_router
)
from app.database import init_db, close_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: web.Application):
    """Жизненный цикл приложения"""
    # Инициализация при запуске
    await init_db()
    logger.info("База данных инициализирована")
    
    yield
    
    # Очистка при завершении
    await close_db()
    logger.info("База данных закрыта")


async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация бота и диспетчера
        bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
        
        # Выбор хранилища состояний
        if settings.REDIS_URL:
            storage = RedisStorage.from_url(settings.REDIS_URL)
            logger.info("Используется Redis для хранения состояний")
        else:
            storage = MemoryStorage()
            logger.info("Используется память для хранения состояний")
        
        dp = Dispatcher(storage=storage)
        
        # Регистрация middleware
        dp.message.middleware(DatabaseMiddleware())
        dp.callback_query.middleware(DatabaseMiddleware())
        dp.message.middleware(UserMiddleware())
        dp.callback_query.middleware(UserMiddleware())
        
        # Регистрация роутеров
        dp.include_router(text_router)
        dp.include_router(voice_router)
        dp.include_router(photo_router)
        dp.include_router(admin_router)
        dp.include_router(calendar_router)
        dp.include_router(analytics_router)
        
        # Обработка ошибок
        @dp.errors()
        async def errors_handler(update, exception):
            logger.error(f"Ошибка при обработке {update}: {exception}")
            return True
        
        if settings.WEBHOOK_URL:
            # Настройка webhook
            app = web.Application()
            app.router.add_post(f"/{settings.BOT_TOKEN}", SimpleRequestHandler(dp, bot))
            
            # Настройка жизненного цикла
            app.on_startup.append(lambda _: asyncio.create_task(bot.set_webhook(settings.WEBHOOK_URL)))
            app.on_shutdown.append(lambda _: asyncio.create_task(bot.delete_webhook()))
            
            # Запуск webhook
            web.run_app(
                app,
                host=settings.WEBHOOK_HOST,
                port=settings.WEBHOOK_PORT,
                lifespan=lifespan
            )
        else:
            # Запуск в режиме long polling
            logger.info("Запуск бота в режиме long polling")
            await dp.start_polling(bot)
            
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 