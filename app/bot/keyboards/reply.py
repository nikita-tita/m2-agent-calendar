from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная reply клавиатура"""
    
    builder = ReplyKeyboardBuilder()
    
    # Первый ряд - основные функции
    builder.row(
        KeyboardButton(text="📅 Календарь"),
        KeyboardButton(text="➕ Событие")
    )
    
    # Второй ряд - работа с данными
    builder.row(
        KeyboardButton(text="👥 Клиенты"),
        KeyboardButton(text="🏠 Объекты")
    )
    
    # Третий ряд - дополнительные функции
    builder.row(
        KeyboardButton(text="📊 Аналитика"),
        KeyboardButton(text="⚙️ Настройки")
    )
    
    # Четвертый ряд - Mini App календарь
    builder.row(
        KeyboardButton(
            text="🗓️ Календарь М²",
            web_app=WebAppInfo(url="http://127.0.0.1:8000/api/v1/miniapp/")
        )
    )
    
    # Пятый ряд - помощь
    builder.row(
        KeyboardButton(text="❓ Помощь")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="❌ Отменить"))
    
    return builder.as_markup(resize_keyboard=True) 