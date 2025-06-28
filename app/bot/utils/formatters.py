from datetime import datetime
from typing import Optional, Dict, Any
from app.models.user import User
from app.ai.nlp.real_estate_parser import PropertyInfo


def format_welcome_message(user: User) -> str:
    """Форматирует приветственное сообщение"""
    
    greeting = f"👋 Привет, {user.display_name}!"
    
    if user.username:
        welcome_text = f"""
{greeting}

🤖 <b>RealEstate Calendar Bot</b> - ваш AI-ассистент для управления календарем агента недвижимости.

<b>Что умеет бот:</b>
🎤 <b>Голосовое управление</b> - просто скажите "Запланируй показ трешки завтра в два"
📝 <b>Текстовые команды</b> - пишите события обычным текстом
📱 <b>Анализ скриншотов</b> - отправляйте переписки WhatsApp и документы
🧠 <b>AI-автоматизация</b> - оптимизация маршрутов и умные напоминания

<b>Быстрый старт:</b>
• Отправьте голосовое сообщение с описанием события
• Или напишите текст: "Встреча с клиентом в 15:00"
• Или отправьте скриншот переписки

<b>Команды:</b>
/start - Главное меню
/help - Справка
/calendar - Показать календарь
/settings - Настройки

Готов помочь вам организовать работу! 🚀
        """
    else:
        welcome_text = f"""
{greeting}

🤖 <b>RealEstate Calendar Bot</b> - ваш AI-ассистент для управления календарем агента недвижимости.

<b>Рекомендуем:</b>
Установить username в настройках Telegram для более удобной работы с ботом.

<b>Что умеет бот:</b>
🎤 Голосовое управление
📝 Текстовые команды  
📱 Анализ скриншотов
🧠 AI-автоматизация

Готов помочь вам организовать работу! 🚀
        """
    
    return welcome_text.strip()


def format_event_info(event_data: dict) -> str:
    """Форматирует информацию о событии для подтверждения"""
    
    title = event_data.get("title", "Без названия")
    event_type = event_data.get("event_type", "other")
    start_time = event_data.get("start_time")
    location = event_data.get("location")
    description = event_data.get("description")
    
    # Эмодзи для типов событий
    type_emojis = {
        "showing": "🏠",
        "meeting": "👥", 
        "deal": "💰",
        "task": "📋",
        "call": "📞",
        "other": "📅"
    }
    
    emoji = type_emojis.get(event_type, "📅")
    
    text = f"""
{emoji} <b>Создать событие:</b>

<b>Название:</b> {title}
<b>Тип:</b> {event_type.title()}
"""
    
    if start_time:
        if isinstance(start_time, str):
            text += f"<b>Время:</b> {start_time}\n"
        else:
            text += f"<b>Время:</b> {start_time.strftime('%d.%m.%Y %H:%M')}\n"
    
    if location:
        text += f"<b>Место:</b> {location}\n"
    
    if description:
        text += f"<b>Описание:</b> {description}\n"
    
    text += "\nПодтвердите создание события или отредактируйте детали."
    
    return text.strip()


def format_calendar_day(events: list, date: datetime) -> str:
    """Форматирует события на день"""
    
    if not events:
        return f"📅 <b>{date.strftime('%d.%m.%Y')}</b>\n\nНет запланированных событий."
    
    text = f"📅 <b>{date.strftime('%d.%m.%Y')}</b>\n\n"
    
    for i, event in enumerate(events, 1):
        start_time = event.start_time.strftime("%H:%M")
        end_time = event.end_time.strftime("%H:%M") if event.end_time else ""
        
        time_str = f"{start_time}"
        if end_time:
            time_str += f" - {end_time}"
        
        # Эмодзи для типов событий
        type_emojis = {
            "showing": "🏠",
            "meeting": "👥", 
            "deal": "💰",
            "task": "📋",
            "call": "📞",
            "other": "📅"
        }
        
        emoji = type_emojis.get(event.event_type.value, "📅")
        
        text += f"{i}. {emoji} <b>{event.title}</b>\n"
        text += f"   🕐 {time_str}\n"
        
        if event.location:
            text += f"   📍 {event.location}\n"
        
        text += "\n"
    
    return text.strip()


def format_client_info(client_data: dict) -> str:
    """Форматирует информацию о клиенте"""
    
    name = client_data.get("name", "Не указано")
    phone = client_data.get("phone", "Не указан")
    email = client_data.get("email", "Не указан")
    budget = client_data.get("budget")
    areas = client_data.get("areas", [])
    
    text = f"""
👤 <b>Информация о клиенте:</b>

<b>Имя:</b> {name}
<b>Телефон:</b> {phone}
<b>Email:</b> {email}
"""
    
    if budget:
        text += f"<b>Бюджет:</b> {budget:,} ₽\n"
    
    if areas:
        areas_str = ", ".join(areas)
        text += f"<b>Интересующие районы:</b> {areas_str}\n"
    
    return text.strip()


def format_property_info(property_info: PropertyInfo) -> str:
    """Форматирует информацию о недвижимости"""
    if not property_info:
        return "Информация не найдена"
    
    lines = []
    
    if property_info.property_type:
        lines.append(f"🏠 **Тип:** {property_info.property_type}")
    
    if property_info.area:
        lines.append(f"📐 **Площадь:** {property_info.area}")
    
    if property_info.rooms:
        lines.append(f"🛏️ **Комнат:** {property_info.rooms}")
    
    if property_info.price:
        lines.append(f"💰 **Цена:** {property_info.price}")
    
    if property_info.floor:
        lines.append(f"🏢 **Этаж:** {property_info.floor}")
    
    if property_info.address:
        lines.append(f"📍 **Адрес:** {property_info.address}")
    
    if property_info.confidence:
        confidence_percent = int(property_info.confidence * 100)
        lines.append(f"📊 **Уверенность:** {confidence_percent}%")
    
    return "\n".join(lines) if lines else "Информация не извлечена"


def format_validation_result(validation_result: Dict[str, Any]) -> str:
    """Форматирует результат валидации"""
    if not validation_result:
        return ""
    
    lines = []
    
    if validation_result.get("is_valid"):
        lines.append("✅ Данные прошли валидацию")
    else:
        lines.append("⚠️ Найдены проблемы в данных")
    
    errors = validation_result.get("errors", [])
    if errors:
        lines.append("**Ошибки:**")
        for error in errors:
            lines.append(f"• {error}")
    
    warnings = validation_result.get("warnings", [])
    if warnings:
        lines.append("**Предупреждения:**")
        for warning in warnings:
            lines.append(f"• {warning}")
    
    return "\n".join(lines)


def format_ai_status(status: Dict[str, Any]) -> str:
    """Форматирует статус AI сервисов"""
    
    text = "🤖 <b>Статус AI сервисов:</b>\n\n"
    
    # Whisper
    whisper_status = status.get("whisper_client", {})
    if whisper_status.get("available"):
        text += "✅ <b>Распознавание речи:</b> Активно\n"
    else:
        text += "❌ <b>Распознавание речи:</b> Недоступно\n"
    
    # GPT
    gpt_status = status.get("gpt_client", {})
    if gpt_status.get("available"):
        text += "✅ <b>AI анализ:</b> Активен\n"
    else:
        text += "❌ <b>AI анализ:</b> Недоступен\n"
    
    # OCR
    ocr_status = status.get("ocr_client", {})
    if ocr_status.get("available"):
        text += "✅ <b>Распознавание текста:</b> Активно\n"
    else:
        text += "❌ <b>Распознавание текста:</b> Недоступно\n"
    
    # Парсер
    parser_status = status.get("real_estate_parser", {})
    if parser_status.get("available"):
        text += "✅ <b>Парсер недвижимости:</b> Активен\n"
    else:
        text += "❌ <b>Парсер недвижимости:</b> Недоступен\n"
    
    # Общий статус
    overall = status.get("overall", {})
    available = overall.get("available_components", 0)
    total = overall.get("total_components", 4)
    
    text += f"\n📊 <b>Общий статус:</b> {available}/{total} сервисов активно"
    
    if overall.get("fully_operational"):
        text += " 🟢"
    elif available >= 2:
        text += " 🟡"
    else:
        text += " 🔴"
    
    return text.strip()


def format_property_info_legacy(property_data: dict) -> str:
    """Форматирует информацию об объекте недвижимости (legacy)"""
    
    title = property_data.get("title", "Без названия")
    address = property_data.get("address", "Не указан")
    price = property_data.get("price")
    area = property_data.get("area")
    rooms = property_data.get("rooms")
    property_type = property_data.get("type", "other")
    
    # Эмодзи для типов недвижимости
    type_emojis = {
        "apartment": "🏢",
        "house": "🏠",
        "commercial": "🏢",
        "land": "🌍",
        "garage": "🚗",
        "other": "🏠"
    }
    
    emoji = type_emojis.get(property_type, "🏠")
    
    text = f"""
{emoji} <b>Объект недвижимости:</b>

<b>Название:</b> {title}
<b>Адрес:</b> {address}
"""
    
    if price:
        text += f"<b>Цена:</b> {price:,} ₽\n"
    
    if area:
        text += f"<b>Площадь:</b> {area} кв.м\n"
    
    if rooms:
        text += f"<b>Комнаты:</b> {rooms}\n"
    
    return text.strip()


def format_error_message(error: str) -> str:
    """Форматирует сообщение об ошибке"""
    return f"❌ <b>Ошибка:</b> {error}"


def format_success_message(message: str) -> str:
    """Форматирует сообщение об успехе"""
    return f"✅ <b>Успешно:</b> {message}"


def format_event_confirmation(event) -> str:
    """Форматирует подтверждение создания события без ASCII-блоков"""
    
    # Определяем эмодзи для типа события
    type_emojis = {
        "showing": "🏠",
        "meeting": "👥", 
        "deal": "💰",
        "task": "📋",
        "call": "📞",
        "other": "📅"
    }
    
    event_type = getattr(event, 'event_type', 'other')
    emoji = type_emojis.get(event_type, "📅")
    
    # Форматируем дату и время
    start_time = event.start_time.strftime('%d.%m.%Y в %H:%M')
    
    text = f"""✅ СОБЫТИЕ СОЗДАНО

{emoji} Заголовок: {event.title}
📅 Тип события: {event_type.title() if event_type else 'Не указан'}
🕐 Время: {start_time}
👤 Клиент: {'не указан' if not hasattr(event, 'client') or not event.client else event.client}
📍 Место: {event.location if event.location else 'не указано'}

✅ Событие добавлено в календарь
⏰ Напоминание: за 60 минут до события
📱 Уведомление будет отправлено заранее"""
    
    return text.strip()


def format_event_list(events, title: str = "События") -> str:
    """Форматирует список событий"""
    if not events:
        return f"📅 {title}\n\nНет запланированных событий."
    
    text = f"📅 {title}\n\n"
    
    for i, event in enumerate(events, 1):
        start_time = event.start_time.strftime("%H:%M")
        emoji = "📅"
        if hasattr(event, 'event_type'):
            type_emojis = {
                "showing": "🏠",
                "meeting": "👥", 
                "deal": "💰",
                "task": "📋",
                "call": "📞",
                "other": "📅"
            }
            emoji = type_emojis.get(event.event_type, "📅")
        
        text += f"{i}. {emoji} {event.title}\n"
        text += f"   🕐 {start_time}\n"
        
        if event.location:
            text += f"   📍 {event.location}\n"
        
        text += "\n"
    
    return text.strip()


def format_ai_voice_response(result: Dict[str, Any]) -> str:
    """Форматирует ответ AI для голосового сообщения"""
    if "error" in result:
        return f"❌ Ошибка: {result['error']}"
    
    response_parts = []
    
    # Заголовок без ASCII-блоков
    response_parts.append("🎤 Голосовое сообщение обработано")
    
    # Распознанный текст
    transcribed_text = result.get("transcribed_text", "")
    if transcribed_text:
        response_parts.append(
            f"📝 Распознанный текст:\n"
            f"{transcribed_text}"
        )
    
    # Информация о недвижимости
    property_info = result.get("property_info")
    if property_info and hasattr(property_info, 'property_type') and property_info.property_type:
        response_parts.append(
            "🏠 Найденная недвижимость:\n"
            f"{_format_property_info_html(property_info)}"
        )
    
    # GPT анализ
    gpt_enhanced_info = result.get("gpt_enhanced_info")
    if gpt_enhanced_info and "error" not in gpt_enhanced_info:
        response_parts.append(
            "🤖 AI-анализ:\n"
            f"{_format_gpt_info_html(gpt_enhanced_info)}"
        )
    
    if len(response_parts) == 1:  # Только заголовок
        response_parts.append(
            "📭 Результат:\n"
            "Информация о недвижимости не обнаружена.\n\n"
            "💡 Попробуйте сказать более четко или упомянуть детали объекта"
        )
    
    return "\n\n".join(response_parts)


def format_ai_image_response(result: Dict[str, Any]) -> str:
    """Форматирует ответ AI для изображения"""
    if "error" in result:
        return f"❌ Ошибка: {result['error']}"
    
    response_parts = []
    
    # Заголовок без ASCII-блоков
    response_parts.append("📸 Изображение обработано")
    
    # OCR результат
    ocr_result = result.get("ocr_result", {})
    extracted_text = result.get("extracted_text", "")
    
    if extracted_text:
        confidence = ocr_result.get("confidence", 0)
        response_parts.append(
            f"📝 Распознанный текст:\n"
            f"{extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}\n"
            f"📊 Качество распознавания: {confidence:.1%}"
        )
    else:
        response_parts.append(
            "📝 Распознанный текст:\n"
            "Текст не обнаружен"
        )
    
    # Информация о недвижимости
    property_info = result.get("property_info")
    if property_info and hasattr(property_info, 'property_type') and property_info.property_type:
        response_parts.append(
            "🏠 Найденная недвижимость:\n"
            f"{_format_property_info_html(property_info)}"
        )
    
    # GPT анализ
    gpt_enhanced_info = result.get("gpt_enhanced_info")
    if gpt_enhanced_info and "error" not in gpt_enhanced_info:
        response_parts.append(
            "🤖 AI-анализ:\n"
            f"{_format_gpt_info_html(gpt_enhanced_info)}"
        )
    
    if not property_info or not hasattr(property_info, 'property_type') or not property_info.property_type:
        if extracted_text:
            response_parts.append(
                "📭 Результат:\n"
                "Информация о недвижимости не обнаружена.\n\n"
                "💡 Убедитесь, что на изображении есть объявление о недвижимости"
            )
        else:
            response_parts.append(
                "📭 Результат:\n"
                "Текст на изображении не распознан.\n\n"
                "💡 Проверьте качество изображения и четкость текста"
            )
    
    return "\n\n".join(response_parts)


def _format_property_info_html(property_info) -> str:
    """Форматирует информацию о недвижимости в HTML"""
    lines = []
    
    if hasattr(property_info, 'property_type') and property_info.property_type:
        lines.append(f"🏠 <b>Тип:</b> {property_info.property_type}")
    
    if hasattr(property_info, 'area') and property_info.area:
        lines.append(f"📐 <b>Площадь:</b> {property_info.area}")
    
    if hasattr(property_info, 'rooms') and property_info.rooms:
        lines.append(f"🛏️ <b>Комнат:</b> {property_info.rooms}")
    
    if hasattr(property_info, 'price') and property_info.price:
        lines.append(f"💰 <b>Цена:</b> {property_info.price}")
    
    if hasattr(property_info, 'floor') and property_info.floor:
        lines.append(f"🏢 <b>Этаж:</b> {property_info.floor}")
    
    if hasattr(property_info, 'address') and property_info.address:
        lines.append(f"📍 <b>Адрес:</b> {property_info.address}")
    
    if hasattr(property_info, 'confidence') and property_info.confidence:
        confidence_percent = int(property_info.confidence * 100)
        lines.append(f"📊 <b>Уверенность:</b> {confidence_percent}%")
    
    return "\n".join(lines) if lines else "Информация не извлечена"


def _format_gpt_info_html(gpt_info: Dict[str, Any]) -> str:
    """Форматирует GPT информацию в HTML"""
    lines = []
    
    # Основные поля
    key_mapping = {
        "property_type": ("🏠", "Тип"),
        "address": ("📍", "Адрес"),
        "area": ("📐", "Площадь"),
        "rooms": ("🛏️", "Комнат"),
        "price": ("💰", "Цена"),
        "floor": ("🏢", "Этаж"),
        "description": ("📝", "Описание"),
        "contact": ("📞", "Контакт")
    }
    
    for key, value in gpt_info.items():
        if value and key in key_mapping and key not in ["error", "confidence"]:
            emoji, label = key_mapping[key]
            # Ограничиваем длину описания
            if key == "description" and len(str(value)) > 100:
                value = str(value)[:100] + "..."
            lines.append(f"{emoji} <b>{label}:</b> {value}")
    
    # Уверенность
    confidence = gpt_info.get("confidence")
    if confidence:
        try:
            confidence_percent = int(float(confidence) * 100)
            lines.append(f"📊 <b>Уверенность:</b> {confidence_percent}%")
        except (ValueError, TypeError):
            pass
    
    return "\n".join(lines) if lines else "Анализ не дал результатов" 