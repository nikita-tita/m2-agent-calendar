"""
Утилиты форматирования сообщений
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pytz

from app.models.calendar import CalendarEvent, EventType, EventStatus
from app.schemas.calendar import EventSuggestion


def format_event(event: CalendarEvent) -> str:
    """Форматирование события для отображения"""
    try:
        # Основная информация
        text = f"🎯 <b>{event.title}</b>\n"
        
        # Дата и время
        text += f"📅 Дата: {event.start_time.strftime('%d.%m.%Y')}\n"
        text += f"🕐 Время: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n"
        text += f"⏱️ Продолжительность: {event.duration_minutes} мин\n"
        
        # Тип события
        type_icon = get_event_type_icon(event.event_type)
        text += f"{type_icon} Тип: {EventType(event.event_type).value.title()}\n"
        
        # Статус
        status_icon = get_status_icon(event.status)
        text += f"{status_icon} Статус: {EventStatus(event.status).value.title()}\n"
        
        # Место проведения
        if event.location:
            text += f"📍 Место: {event.location}\n"
        
        # Информация о клиенте
        if event.client_name:
            text += f"👤 Клиент: {event.client_name}\n"
        
        if event.client_phone:
            text += f"📞 Телефон: {event.client_phone}\n"
        
        # Описание
        if event.description:
            text += f"📝 Описание: {event.description}\n"
        
        # Заметки
        if event.notes:
            text += f"📋 Заметки: {event.notes}\n"
        
        # Дополнительная информация
        if event.is_today:
            text += "📌 <b>Сегодня!</b>\n"
        
        if event.is_overdue:
            text += "⚠️ <b>Просрочено!</b>\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования события: {e}"


def format_events_list(events: List[CalendarEvent], title: str = "События") -> str:
    """Форматирование списка событий"""
    try:
        if not events:
            return f"📅 <b>{title}</b>\n\n✅ Нет событий для отображения."
        
        text = f"📅 <b>{title}</b>\n\n"
        
        for i, event in enumerate(events, 1):
            text += f"{i}. <b>{event.title}</b>\n"
            text += f"   🕐 {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n"
            
            if event.location:
                text += f"   📍 {event.location}\n"
            
            if event.client_name:
                text += f"   👤 {event.client_name}\n"
            
            # Статус
            status_icon = get_status_icon(event.status)
            text += f"   {status_icon} {EventStatus(event.status).value.title()}\n"
            
            text += "\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования списка событий: {e}"


def format_time_slot(suggestion: EventSuggestion, index: int = 1) -> str:
    """Форматирование временного слота"""
    try:
        start_time = suggestion.start_time.strftime("%H:%M")
        end_time = suggestion.end_time.strftime("%H:%M")
        confidence = suggestion.confidence
        
        text = f"{index}. <b>{start_time} - {end_time}</b>\n"
        text += f"   🎯 Уверенность: {confidence:.0%}\n"
        text += f"   💡 {suggestion.reason}\n\n"
        
        return text
        
    except Exception as e:
        return f"❌ Ошибка форматирования временного слота: {e}"


def format_calendar_stats(stats: Dict[str, Any]) -> str:
    """Форматирование статистики календаря"""
    try:
        text = "📊 <b>Статистика календаря</b>\n\n"
        
        # Основная статистика
        text += f"📈 Всего событий: {stats['total_events']}\n"
        text += f"✅ Завершено: {stats['completed_events']}\n"
        text += f"❌ Отменено: {stats['cancelled_events']}\n"
        text += f"📅 Предстоящих: {stats['upcoming_events']}\n"
        text += f"⏱️ Средняя продолжительность: {stats['average_duration']:.0f} мин\n\n"
        
        # Статистика по типам
        text += "📅 <b>По типам событий:</b>\n"
        for event_type, count in stats['events_by_type'].items():
            if count > 0:
                icon = get_event_type_icon(event_type)
                text += f"{icon} {event_type.title()}: {count}\n"
        
        # Загруженные часы
        if stats.get('busy_hours'):
            text += "\n🕐 <b>Загруженные часы:</b>\n"
            busy_hours = sorted(stats['busy_hours'].items(), key=lambda x: x[1], reverse=True)
            for hour, count in busy_hours[:5]:  # Топ-5 часов
                text += f"   {hour:02d}:00 - {count} событий\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования статистики: {e}"


def format_daily_schedule(events: List[CalendarEvent]) -> str:
    """Форматирование ежедневного расписания"""
    try:
        if not events:
            return "✅ Сегодня у вас нет запланированных событий."
        
        text = "📅 <b>Расписание на сегодня</b>\n\n"
        
        # Группировка по времени
        morning_events = []
        afternoon_events = []
        evening_events = []
        
        for event in events:
            hour = event.start_time.hour
            if 6 <= hour < 12:
                morning_events.append(event)
            elif 12 <= hour < 18:
                afternoon_events.append(event)
            else:
                evening_events.append(event)
        
        # Утренние события
        if morning_events:
            text += "🌅 <b>Утро:</b>\n"
            for event in morning_events:
                text += format_schedule_event(event)
            text += "\n"
        
        # Дневные события
        if afternoon_events:
            text += "☀️ <b>День:</b>\n"
            for event in afternoon_events:
                text += format_schedule_event(event)
            text += "\n"
        
        # Вечерние события
        if evening_events:
            text += "🌆 <b>Вечер:</b>\n"
            for event in evening_events:
                text += format_schedule_event(event)
            text += "\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования расписания: {e}"


def format_schedule_event(event: CalendarEvent) -> str:
    """Форматирование события в расписании"""
    try:
        text = f"   🕐 <b>{event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}</b>\n"
        text += f"   🎯 {event.title}\n"
        
        if event.location:
            text += f"   📍 {event.location}\n"
        
        if event.client_name:
            text += f"   👤 {event.client_name}\n"
        
        text += "\n"
        return text
        
    except Exception as e:
        return f"   ❌ Ошибка форматирования события: {e}\n"


def format_weekly_summary(stats: Dict[str, Any]) -> str:
    """Форматирование еженедельной сводки"""
    try:
        text = "📊 <b>Еженедельная сводка</b>\n\n"
        
        # Основные показатели
        text += f"📈 Всего событий: {stats['total_events']}\n"
        text += f"✅ Завершено: {stats['completed_events']}\n"
        text += f"❌ Отменено: {stats['cancelled_events']}\n"
        text += f"📅 Предстоящих: {stats['upcoming_events']}\n\n"
        
        # Статистика по типам
        text += "📅 <b>По типам событий:</b>\n"
        for event_type, count in stats['events_by_type'].items():
            if count > 0:
                icon = get_event_type_icon(event_type)
                text += f"{icon} {event_type.title()}: {count}\n"
        
        # Средняя продолжительность
        if stats.get('average_duration', 0) > 0:
            text += f"\n⏱️ Средняя продолжительность: {stats['average_duration']:.0f} мин"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования еженедельной сводки: {e}"


def format_property_info(property_data: Dict[str, Any]) -> str:
    """Форматирование информации о недвижимости"""
    try:
        text = "🏠 <b>Информация о недвижимости</b>\n\n"
        
        # Основная информация
        if property_data.get('type'):
            text += f"📋 Тип: {property_data['type']}\n"
        
        if property_data.get('address'):
            text += f"📍 Адрес: {property_data['address']}\n"
        
        if property_data.get('price'):
            text += f"💰 Цена: {property_data['price']}\n"
        
        if property_data.get('area'):
            text += f"📐 Площадь: {property_data['area']}\n"
        
        if property_data.get('rooms'):
            text += f"🛏️ Комнат: {property_data['rooms']}\n"
        
        if property_data.get('floor'):
            text += f"🏢 Этаж: {property_data['floor']}\n"
        
        if property_data.get('description'):
            text += f"\n📝 Описание: {property_data['description']}\n"
        
        # Дополнительные характеристики
        if property_data.get('features'):
            text += f"\n✨ Особенности:\n"
            for feature in property_data['features']:
                text += f"   • {feature}\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования информации о недвижимости: {e}"


def format_ai_response(response: Dict[str, Any]) -> str:
    """Форматирование ответа AI"""
    try:
        text = "🤖 <b>Ответ AI</b>\n\n"
        
        if response.get('confidence'):
            confidence = response['confidence']
            if confidence >= 0.8:
                text += f"🎯 Высокая уверенность ({confidence:.0%})\n\n"
            elif confidence >= 0.6:
                text += f"✅ Средняя уверенность ({confidence:.0%})\n\n"
            else:
                text += f"⚠️ Низкая уверенность ({confidence:.0%})\n\n"
        
        if response.get('extracted_data'):
            text += "📋 <b>Извлеченные данные:</b>\n"
            for key, value in response['extracted_data'].items():
                if value:
                    text += f"   • {key}: {value}\n"
            text += "\n"
        
        if response.get('answer'):
            text += f"💬 <b>Ответ:</b>\n{response['answer']}\n\n"
        
        if response.get('suggestions'):
            text += "💡 <b>Рекомендации:</b>\n"
            for suggestion in response['suggestions']:
                text += f"   • {suggestion}\n"
        
        return text.strip()
        
    except Exception as e:
        return f"❌ Ошибка форматирования ответа AI: {e}"


def format_error_message(error: str, context: str = "") -> str:
    """Форматирование сообщения об ошибке"""
    try:
        text = "❌ <b>Произошла ошибка</b>\n\n"
        
        if context:
            text += f"Контекст: {context}\n\n"
        
        text += f"Ошибка: {error}\n\n"
        text += "Попробуйте еще раз или обратитесь к администратору."
        
        return text
        
    except Exception as e:
        return f"❌ Критическая ошибка форматирования: {e}"


def format_success_message(message: str, details: str = "") -> str:
    """Форматирование сообщения об успехе"""
    try:
        text = "✅ <b>Успешно!</b>\n\n"
        text += f"{message}\n"
        
        if details:
            text += f"\n{details}"
        
        return text
        
    except Exception as e:
        return f"❌ Ошибка форматирования: {e}"


def get_event_type_icon(event_type: str) -> str:
    """Получение иконки для типа события"""
    icons = {
        "meeting": "🤝",
        "showing": "🏠",
        "call": "📞",
        "consultation": "💼",
        "contract": "📋",
        "other": "📝"
    }
    return icons.get(event_type, "📝")


def get_status_icon(status: str) -> str:
    """Получение иконки для статуса события"""
    icons = {
        "scheduled": "📅",
        "in_progress": "🔄",
        "completed": "✅",
        "cancelled": "❌",
        "rescheduled": "🔄"
    }
    return icons.get(status, "📝")


def format_duration(minutes: int) -> str:
    """Форматирование продолжительности"""
    try:
        if minutes < 60:
            return f"{minutes} мин"
        elif minutes == 60:
            return "1 час"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} ч"
            else:
                return f"{hours}ч {remaining_minutes}м"
        
    except Exception as e:
        return f"{minutes} мин"


def format_relative_time(dt: datetime) -> str:
    """Форматирование относительного времени"""
    try:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        diff = dt - now
        
        if diff.total_seconds() < 0:
            return "прошло"
        
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        if days > 0:
            return f"через {days} дн"
        elif hours > 0:
            return f"через {hours}ч"
        elif minutes > 0:
            return f"через {minutes}м"
        else:
            return "сейчас"
        
    except Exception as e:
        return dt.strftime("%H:%M") 