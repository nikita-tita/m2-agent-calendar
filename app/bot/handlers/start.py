"""
Упрощённый обработчик команды /start
"""
import logging
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.models.user import User
from app.bot.keyboards.inline import get_main_menu_keyboard, get_help_keyboard
from app.bot.keyboards.reply import get_main_reply_keyboard
from app.database import get_async_session
from app.services.user_service import get_or_create_user

logger = logging.getLogger(__name__)
router = Router()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
) -> User:
    """Получение или создание пользователя"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalars().first()

    if user:
        return user
    
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Упрощённая команда старт"""
    try:
        async for session in get_async_session():
            # Создаём/получаем пользователя
            user = await get_or_create_user(
                session=session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            
            logger.info(f"[START] Пользователь найден/создан: {user.id} ({user.username})")
            
            # Создаём клавиатуру с календарём
            calendar_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📅 Мой календарь",
                            web_app=WebAppInfo(url="https://your-domain.com/miniapp/main.html")
                        )
                    ],
                    [
                        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
                    ]
                ]
            )
            
            # Отправляем приветствие
            welcome_text = (
                f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
                "🤖 Я ваш персональный календарь-помощник.\n\n"
                "<b>Что я умею:</b>\n"
                "📝 Создавать события из текста\n"
                "🎤 Распознавать голосовые сообщения\n"
                "📸 Читать текст с изображений\n"
                "📅 Показывать календарь событий\n\n"
                "<b>Просто напишите:</b>\n"
                "• «Встреча завтра в 15:00»\n"
                "• «Звонок клиенту сегодня в 17:30»\n"
                "• «Показ квартиры в понедельник»\n\n"
                "Или отправьте голосовое сообщение/фото 📱"
            )
            
            await message.answer(
                welcome_text,
                reply_markup=calendar_keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"[START] Приветственное сообщение отправлено пользователю {user.id}")
            break
            
    except Exception as e:
        logger.error(f"[START] Ошибка: {e}")
        await message.answer(
            "❌ Произошла ошибка при запуске.\n"
            "Попробуйте ещё раз через несколько секунд.",
            parse_mode="HTML"
        )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    logger.info(f"[HELP] Получена команда /help от пользователя {message.from_user.id}")
    """Обработчик команды /help"""
    
    help_text = """
📖 <b>Подробное руководство пользователя</b>

<b>🎯 ОСНОВНЫЕ ФУНКЦИИ:</b>

📅 <b>КАЛЕНДАРЬ</b>
• Просмотр всех запланированных событий
• Фильтрация по датам и типам событий
• Быстрый переход к конкретному дню

➕ <b>СОЗДАНИЕ СОБЫТИЙ</b>
• Текст: "Показ 2-комн кв завтра в 15:00"
• Голос: запишите голосовое с деталями
• Фото: отправьте скриншот переписки с клиентом

👥 <b>КЛИЕНТЫ</b>
• База контактов покупателей/продавцов
• История взаимодействий
• Заметки и предпочтения

🏠 <b>ОБЪЕКТЫ</b>
• Каталог недвижимости
• Характеристики и фото
• Статус продаж

📊 <b>АНАЛИТИКА</b>
• Статистика показов
• Конверсия в сделки
• Доходы по периодам

<b>💡 ПРИМЕРЫ КОМАНД:</b>

📝 <b>Текстовые сообщения:</b>
• "Показ трешки на Пушкина завтра в 14:00"
• "Звонок Петрову через час"
• "Встреча в офисе в понедельник в 10:00"
• "Подписание договора 25 числа в 16:30"

🎤 <b>Голосовые сообщения:</b>
Скажите: "Запланируй показ двушки клиенту Иванову завтра в два часа дня"

📸 <b>Фото и скриншоты:</b>
• Скриншот WhatsApp с договоренностью
• Фото документов или планировки
• Скан договора или справки

<b>⚙️ КОМАНДЫ:</b>
/start - главное меню
/help - эта справка
/calendar - открыть календарь
/settings - настройки

<b>🆘 Нужна помощь?</b>
Напишите "помощь" или обратитесь к администратору
    """
    
    await message.answer(
        help_text,
        reply_markup=get_help_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("settings"))
async def cmd_settings(message: types.Message) -> None:
    logger.info(f"[SETTINGS] Получена команда /settings от пользователя {message.from_user.id}")
    """Обработчик команды /settings"""
    
    settings_text = """
⚙️ <b>Настройки</b>

Здесь вы можете настроить:
• Временную зону
• Интервалы напоминаний
• Уведомления
• Язык интерфейса

<i>Функция в разработке...</i>
    """
    
    await message.answer(settings_text, parse_mode="HTML")


# Обработчики кнопок меню
@router.message(F.text == "📅 Календарь")
async def menu_calendar(message: types.Message):
    """Обработчик кнопки Календарь"""
    text = """
📅 <b>Ваш календарь</b>

<b>Что вы можете делать:</b>
• Просматривать события на сегодня
• Планировать встречи на завтра
• Искать свободное время
• Получать напоминания

<b>Быстрые команды:</b>
• "показать календарь на завтра"
• "что у меня в понедельник"
• "свободное время на этой неделе"

<i>Полная версия календаря в разработке...</i>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Событие")
async def menu_create_event(message: types.Message):
    """Обработчик кнопки Создать событие"""
    text = """
➕ <b>Создание нового события</b>

<b>Просто напишите или скажите:</b>

📝 <b>Примеры текста:</b>
• "Показ 3-комн квартиры завтра в 15:00"
• "Встреча с Петровыми в офисе в понедельник в 10:00"
• "Звонок клиенту Иванову через час"
• "Подписание договора 25 числа в 16:30"

🎤 <b>Голосовое сообщение:</b>
Запишите голосовое с деталями встречи

📸 <b>Отправьте фото:</b>
Скриншот переписки или документа

<b>Напишите ваше событие прямо сейчас!</b>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Клиенты")
async def menu_clients(message: types.Message):
    """Обработчик кнопки Клиенты"""
    text = """
👥 <b>Управление клиентами</b>

<b>Функции:</b>
• База контактов покупателей и продавцов
• История встреч и звонков
• Заметки и предпочтения
• Статус сделок

<b>Команды:</b>
• "добавить клиента Иванов +79991234567"
• "найти клиента Петров"
• "показать всех клиентов"

<i>Модуль клиентов в разработке...</i>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🏠 Объекты")
async def menu_properties(message: types.Message):
    """Обработчик кнопки Объекты"""
    text = """
🏠 <b>Каталог недвижимости</b>

<b>Возможности:</b>
• Добавление новых объектов
• Характеристики и фотографии
• Статус продаж
• История показов

<b>Команды:</b>
• "добавить квартиру 2-комн Ленина 15"
• "показать объекты в продаже"
• "объект продан"

<i>Модуль объектов в разработке...</i>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Аналитика")
async def menu_analytics(message: types.Message):
    """Обработчик кнопки Аналитика"""
    text = """
📊 <b>Аналитика и отчеты</b>

<b>Доступные отчеты:</b>
• Количество показов за период
• Конверсия в сделки
• Доходы по месяцам
• Эффективность работы

<b>Команды:</b>
• "статистика за месяц"
• "сколько показов за неделю"
• "отчет по продажам"

<i>Модуль аналитики в разработке...</i>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "⚙️ Настройки")
async def menu_settings(message: types.Message):
    """Обработчик кнопки Настройки"""
    text = """
⚙️ <b>Настройки профиля</b>

<b>Доступные настройки:</b>
• Временная зона
• Уведомления и напоминания
• Язык интерфейса
• Рабочие часы

<b>Команды:</b>
• "установить часовой пояс Москва"
• "включить уведомления"
• "рабочие часы с 9 до 18"

<i>Настройки в разработке...</i>
    """
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "❓ Помощь")
async def menu_help(message: types.Message):
    """Обработчик кнопки Помощь"""
    # Используем существующий обработчик help
    await cmd_help(message)


def register_handlers(dp: Router) -> None:
    """Регистрация обработчиков"""
    dp.include_router(router) 