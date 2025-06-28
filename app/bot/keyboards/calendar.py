from datetime import datetime, timedelta
from typing import Optional, List
from calendar import monthrange

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_quick_actions_keyboard():
    """Основные быстрые действия"""
    builder = InlineKeyboardBuilder()
    
    # Основные действия в две колонки
    builder.button(text="📅 Календарь", callback_data="show_calendar")
    builder.button(text="📋 События", callback_data="my_events")
    
    # Создание события отдельно
    builder.button(text="➕ Создать событие", callback_data="create_event")
    
    # Mini App календарь
    builder.button(
        text="🗓️ Открыть календарь", 
        web_app=WebAppInfo(url="http://127.0.0.1:8000/api/v1/miniapp/")
    )
    
    builder.adjust(2, 1, 1)  # Первый ряд - 2 кнопки, второй - 1, третий - 1
    return builder.as_markup()

def get_calendar_keyboard():
    """Простой календарь с быстрыми кнопками"""
    builder = InlineKeyboardBuilder()
    
    # Быстрые кнопки для дат
    builder.button(text="📅 Сегодня", callback_data="date_today")
    builder.button(text="📅 Завтра", callback_data="date_tomorrow")
    
    builder.button(text="📅 Понедельник", callback_data="date_monday")
    builder.button(text="📅 Вторник", callback_data="date_tuesday")
    
    builder.button(text="📅 Среда", callback_data="date_wednesday") 
    builder.button(text="📅 Четверг", callback_data="date_thursday")
    
    builder.button(text="📅 Пятница", callback_data="date_friday")
    builder.button(text="📅 Выходные", callback_data="date_weekend")
    
    # Навигация
    builder.button(text="↩️ Назад", callback_data="back_to_main")
    
    builder.adjust(2, 2, 2, 2, 1)  # 2-2-2-2-1
    return builder.as_markup()

def get_time_keyboard():
    """Выбор времени"""
    builder = InlineKeyboardBuilder()
    
    # Популярные времена
    times = [
        ("9:00", "time_0900"),
        ("10:00", "time_1000"),
        ("11:00", "time_1100"),
        ("12:00", "time_1200"),
        ("13:00", "time_1300"),
        ("14:00", "time_1400"),
        ("15:00", "time_1500"),
        ("16:00", "time_1600"),
        ("17:00", "time_1700"),
        ("18:00", "time_1800"),
        ("19:00", "time_1900"),
        ("20:00", "time_2000"),
    ]
    
    for time_text, callback in times:
        builder.button(text=time_text, callback_data=callback)
    
    # Свое время
    builder.button(text="⏰ Другое время", callback_data="time_custom")
    
    # Назад
    builder.button(text="↩️ Назад", callback_data="show_calendar")
    
    builder.adjust(3, 3, 3, 3, 1, 1)  # 3-3-3-3-1-1
    return builder.as_markup()

def get_main_menu_keyboard():
    """Главное меню с понятными кнопками"""
    builder = InlineKeyboardBuilder()
    
    # Основные функции
    builder.button(text="📅 Календарь", callback_data="menu_calendar")
    builder.button(text="➕ Создать", callback_data="menu_create_event")
    
    # Управление данными
    builder.button(text="👥 Клиенты", callback_data="menu_clients")
    builder.button(text="🏠 Объекты", callback_data="menu_properties")
    
    # Аналитика и настройки
    builder.button(text="📊 Аналитика", callback_data="menu_analytics")
    builder.button(text="⚙️ Настройки", callback_data="menu_settings")
    
    # Помощь
    builder.button(text="❓ Помощь", callback_data="menu_help")
    
    builder.adjust(2, 2, 2, 1)  # 2-2-2-1
    return builder.as_markup()

def get_event_types_keyboard():
    """Типы событий"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🤝 Встреча", callback_data="type_meeting")
    builder.button(text="🏠 Показ", callback_data="type_showing")
    
    builder.button(text="📞 Звонок", callback_data="type_call")
    builder.button(text="📝 Задача", callback_data="type_task")
    
    builder.button(text="💰 Сделка", callback_data="type_deal")
    builder.button(text="📋 Другое", callback_data="type_other")
    
    builder.button(text="↩️ Назад", callback_data="create_event")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

# Функции для совместимости (могут использоваться в других частях)
def get_event_actions_keyboard(event_id: int, action: str):
    """Действия с событием"""
    builder = InlineKeyboardBuilder()
    
    if action == "delete":
        builder.button(text="❌ Да, удалить", callback_data=f"confirm_delete_{event_id}")
        builder.button(text="↩️ Отмена", callback_data="my_events")
    elif action == "created":
        builder.button(text="✏️ Изменить", callback_data=f"event_edit_{event_id}")
        builder.button(text="❌ Удалить", callback_data=f"event_delete_{event_id}")
        builder.button(text="📅 К календарю", callback_data="show_calendar")
    
    builder.adjust(1)
    return builder.as_markup()

def get_my_events_keyboard(events):
    """Список событий (упрощенный)"""
    return get_quick_actions_keyboard()  # Используем быстрые действия 