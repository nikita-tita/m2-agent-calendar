"""
Упрощённый главный файл бота
"""
import asyncio
import logging
import os

# Загружаем переменные окружения из .env файла ПЕРВЫМ ДЕЛОМ
from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import callback, photo, start, text, voice
from app.bot.middlewares.db import DatabaseMiddleware
from app.bot.middlewares.logging import LoggingMiddleware
from app.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверяем наличие обязательных переменных окружения
if not os.getenv("TELEGRAM_BOT_TOKEN"):
    logger.error("TELEGRAM_BOT_TOKEN не найден! Установите переменную окружения.")
    print("❌ Необходим TELEGRAM_BOT_TOKEN!")
    print("💡 Получите токен у @BotFather и установите переменную:")
    print("   export TELEGRAM_BOT_TOKEN='your-bot-token'")
    exit(1)

if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY не найден! AI-функции будут ограничены.")
    print("⚠️  OPENAI_API_KEY не настроен!")
    print("💡 Для полной функциональности установите:")
    print("   export OPENAI_API_KEY='sk-your-openai-key'")

try:
    settings = settings
except Exception as e:
    logger.error(f"Ошибка в настройках: {e}")
    print(f"❌ Ошибка конфигурации: {e}")
    exit(1)
from app.database import create_pool

# Обновляем уровень логирования из настроек
logger.setLevel(settings.LOG_LEVEL.upper())

async def main():
    """Главная функция бота"""
    
    # Создаём бота и диспетчер
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Подключаем middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(LoggingMiddleware())
    
    # Регистрируем обработчики
    start.register_handlers(dp)
    text.register_handlers(dp)
    voice.register_handlers(dp)
    photo.register_handlers(dp)
    callback.register_handlers(dp)
    
    logger.info("🤖 Упрощённый календарь-бот запущен!")
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 