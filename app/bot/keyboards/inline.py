from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
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
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    """Основная inline клавиатура для главного меню"""
    return get_main_menu_keyboard()


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Календарь", web_app=WebAppInfo(url="https://your-domain.com/miniapp/main.html"))
            ],
            [
                InlineKeyboardButton(text="📝 Примеры команд", callback_data="help_examples")
            ]
        ]
    )


def get_calendar_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для открытия календаря"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Открыть календарь",
                    web_app=WebAppInfo(url="https://your-domain.com/miniapp/main.html")
                )
            ],
            [
                InlineKeyboardButton(text="📝 Создать событие", callback_data="create_event")
            ]
        ]
    )


def get_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Простая кнопка Назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Назад", callback_data=callback_data)
    return builder.as_markup()


def get_voice_actions_keyboard(transcribed_text: str):
    """Действия с голосовым сообщением"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Создать событие", callback_data="create_from_voice")
    builder.button(text="🤖 Спросить ИИ", callback_data="ask_ai")
    builder.button(text="📋 Сохранить", callback_data="save_note")
    
    builder.adjust(1)
    return builder.as_markup()


def get_image_actions_keyboard(extracted_text: str):
    """Действия с изображением"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Создать событие", callback_data="create_from_image")
    builder.button(text="🤖 Анализ ИИ", callback_data="analyze_image")
    builder.button(text="📋 Сохранить текст", callback_data="save_extracted_text")
    
    builder.adjust(1)
    return builder.as_markup()


def get_property_actions_keyboard(extracted_text: str):
    """Действия с информацией о недвижимости"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Создать показ", callback_data="create_showing")
    builder.button(text="📞 Запланировать звонок", callback_data="create_call")
    builder.button(text="💾 Сохранить объект", callback_data="save_property")
    
    builder.adjust(1)
    return builder.as_markup()


def get_ai_status_keyboard():
    """Статус ИИ функций"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Обновить", callback_data="refresh_ai_status")
    builder.button(text="↩️ Назад", callback_data="back_to_main")
    
    builder.adjust(1)
    return builder.as_markup()


def get_event_confirmation_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения создания события"""
    
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Подтвердить",
        callback_data=f"event_confirm_{event_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="✏️ Редактировать",
        callback_data=f"event_edit_{event_id}"
    ))
    
    builder.row()
    
    builder.add(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data=f"event_cancel_{event_id}"
    ))
    
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🕐 Временная зона",
        callback_data="settings_timezone"
    ))
    builder.add(InlineKeyboardButton(
        text="🔔 Напоминания",
        callback_data="settings_reminders"
    ))
    
    builder.row()
    
    builder.add(InlineKeyboardButton(
        text="🌐 Язык",
        callback_data="settings_language"
    ))
    builder.add(InlineKeyboardButton(
        text="📱 Уведомления",
        callback_data="settings_notifications"
    ))
    
    builder.row()
    
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="menu_main"
    ))
    
    return builder.as_markup()


def get_event_actions_keyboard(event_id: int, action_type: str = "created") -> InlineKeyboardMarkup:
    """Клавиатура для действий с событием"""
    buttons = []
    
    if action_type == "created":
        buttons = [
            [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"event_edit_{event_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"event_delete_{event_id}")],
            [InlineKeyboardButton(text="📅 Календарь", web_app=WebAppInfo(url="https://your-domain.com/miniapp/main.html"))]
        ]
    elif action_type == "delete":
        buttons = [
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"event_confirm_delete_{event_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="event_cancel_delete")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 