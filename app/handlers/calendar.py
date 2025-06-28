"""
Обработчики команд календаря
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.calendar_service import CalendarService, EventValidationError, CalendarConflictError
from app.models.calendar import EventType, EventStatus
from app.models.user import User
from app.keyboards.calendar import (
    get_calendar_main_keyboard,
    get_event_type_keyboard,
    get_event_actions_keyboard,
    get_calendar_navigation_keyboard,
    get_time_slots_keyboard
)
from app.utils.formatters import format_event, format_events_list, format_time_slot
from app.database import get_db

logger = logging.getLogger(__name__)
router = Router()


class CreateEventStates(StatesGroup):
    """Состояния создания события"""
    waiting_for_type = State()
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_duration = State()
    waiting_for_location = State()
    waiting_for_client_name = State()
    waiting_for_client_phone = State()
    waiting_for_description = State()
    waiting_for_confirmation = State()


class EditEventStates(StatesGroup):
    """Состояния редактирования события"""
    waiting_for_field = State()
    waiting_for_new_value = State()


@router.message(Command("calendar"))
async def calendar_main(message: Message, fsm_context: FSMContext):
    """Главное меню календаря"""
    try:
        await fsm_context.clear()
        
        keyboard = get_calendar_main_keyboard()
        
        await message.answer(
            "📅 <b>Календарь событий</b>\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в главном меню календаря: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(Command("today"))
async def show_today_events(message: Message):
    """Показать события на сегодня"""
    try:
        async with get_db() as db:
            calendar_service = CalendarService(db)
            
            # Получение пользователя
            user = await db.get(User, message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return
            
            events = await calendar_service.get_today_events(user.id)
            
            if not events:
                await message.answer(
                    "✅ <b>Сегодня у вас нет запланированных событий</b>\n\n"
                    "Можете создать новое событие командой /create_event",
                    parse_mode="HTML"
                )
            else:
                events_text = format_events_list(events, "Сегодня")
                await message.answer(events_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения событий на сегодня: {e}")
        await message.answer("❌ Произошла ошибка при получении событий.")


@router.message(Command("upcoming"))
async def show_upcoming_events(message: Message):
    """Показать предстоящие события"""
    try:
        async with get_db() as db:
            calendar_service = CalendarService(db)
            
            user = await db.get(User, message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return
            
            events = await calendar_service.get_upcoming_events(user.id, days=7)
            
            if not events:
                await message.answer(
                    "✅ <b>На ближайшую неделю у вас нет запланированных событий</b>\n\n"
                    "Можете создать новое событие командой /create_event",
                    parse_mode="HTML"
                )
            else:
                events_text = format_events_list(events, "Предстоящие события")
                await message.answer(events_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения предстоящих событий: {e}")
        await message.answer("❌ Произошла ошибка при получении событий.")


@router.message(Command("create_event"))
async def start_create_event(message: Message, fsm_context: FSMContext):
    """Начать создание события"""
    try:
        await fsm_context.clear()
        await fsm_context.set_state(CreateEventStates.waiting_for_type)
        
        keyboard = get_event_type_keyboard()
        
        await message.answer(
            "📅 <b>Создание нового события</b>\n\n"
            "Выберите тип события:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка начала создания события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data.startswith("event_type_"))
async def handle_event_type_selection(callback: CallbackQuery, fsm_context: FSMContext):
    """Обработка выбора типа события"""
    try:
        event_type = callback.data.replace("event_type_", "")
        
        await fsm_context.update_data(event_type=event_type)
        await fsm_context.set_state(CreateEventStates.waiting_for_title)
        
        await callback.message.edit_text(
            f"📝 <b>Введите название события</b>\n\n"
            f"Тип: {EventType(event_type).value}\n"
            f"Пример: Показ квартиры на Ленина, 15",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка выбора типа события: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_title)
async def handle_event_title(message: Message, fsm_context: FSMContext):
    """Обработка названия события"""
    try:
        title = message.text.strip()
        if len(title) < 3:
            await message.answer("❌ Название должно содержать минимум 3 символа.")
            return
        
        await fsm_context.update_data(title=title)
        await fsm_context.set_state(CreateEventStates.waiting_for_date)
        
        await message.answer(
            "📅 <b>Введите дату события</b>\n\n"
            f"Название: {title}\n"
            "Формат: ДД.ММ.ГГГГ\n"
            "Пример: 25.12.2024",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки названия события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_date)
async def handle_event_date(message: Message, fsm_context: FSMContext):
    """Обработка даты события"""
    try:
        date_str = message.text.strip()
        
        try:
            date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
            return
        
        # Проверка, что дата не в прошлом
        if date < datetime.now().date():
            await message.answer("❌ Нельзя создавать события в прошлом.")
            return
        
        await fsm_context.update_data(date=date)
        await fsm_context.set_state(CreateEventStates.waiting_for_time)
        
        await message.answer(
            "🕐 <b>Введите время начала</b>\n\n"
            f"Дата: {date.strftime('%d.%m.%Y')}\n"
            "Формат: ЧЧ:ММ\n"
            "Пример: 14:30",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки даты события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_time)
async def handle_event_time(message: Message, fsm_context: FSMContext):
    """Обработка времени события"""
    try:
        time_str = message.text.strip()
        
        try:
            time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            await message.answer("❌ Неверный формат времени. Используйте формат ЧЧ:ММ")
            return
        
        data = await fsm_context.get_data()
        date = data['date']
        start_time = datetime.combine(date, time)
        
        # Проверка, что время не в прошлом
        if start_time < datetime.now():
            await message.answer("❌ Нельзя создавать события в прошлом.")
            return
        
        await fsm_context.update_data(start_time=start_time)
        await fsm_context.set_state(CreateEventStates.waiting_for_duration)
        
        await message.answer(
            "⏱️ <b>Введите продолжительность в минутах</b>\n\n"
            f"Время начала: {start_time.strftime('%H:%M')}\n"
            "Пример: 60 (для 1 часа)",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки времени события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_duration)
async def handle_event_duration(message: Message, fsm_context: FSMContext):
    """Обработка продолжительности события"""
    try:
        try:
            duration = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введите число минут.")
            return
        
        if duration < 15 or duration > 480:  # От 15 минут до 8 часов
            await message.answer("❌ Продолжительность должна быть от 15 минут до 8 часов.")
            return
        
        data = await fsm_context.get_data()
        start_time = data['start_time']
        end_time = start_time + timedelta(minutes=duration)
        
        await fsm_context.update_data(duration=duration, end_time=end_time)
        await fsm_context.set_state(CreateEventStates.waiting_for_location)
        
        await message.answer(
            "📍 <b>Введите место проведения</b>\n\n"
            f"Время: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
            "Пример: ул. Ленина, 15, кв. 45\n"
            "Или нажмите /skip для пропуска",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки продолжительности события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_location)
async def handle_event_location(message: Message, fsm_context: FSMContext):
    """Обработка места проведения"""
    try:
        location = message.text.strip() if message.text != "/skip" else None
        
        await fsm_context.update_data(location=location)
        await fsm_context.set_state(CreateEventStates.waiting_for_client_name)
        
        await message.answer(
            "👤 <b>Введите имя клиента</b>\n\n"
            f"Место: {location or 'Не указано'}\n"
            "Пример: Иван Петров\n"
            "Или нажмите /skip для пропуска",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки места проведения: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_client_name)
async def handle_client_name(message: Message, fsm_context: FSMContext):
    """Обработка имени клиента"""
    try:
        client_name = message.text.strip() if message.text != "/skip" else None
        
        await fsm_context.update_data(client_name=client_name)
        await fsm_context.set_state(CreateEventStates.waiting_for_client_phone)
        
        await message.answer(
            "📞 <b>Введите телефон клиента</b>\n\n"
            f"Клиент: {client_name or 'Не указан'}\n"
            "Формат: +7XXXXXXXXXX\n"
            "Или нажмите /skip для пропуска",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки имени клиента: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_client_phone)
async def handle_client_phone(message: Message, fsm_context: FSMContext):
    """Обработка телефона клиента"""
    try:
        client_phone = message.text.strip() if message.text != "/skip" else None
        
        # Простая валидация телефона
        if client_phone and not (client_phone.startswith('+7') and len(client_phone) == 12):
            await message.answer("❌ Неверный формат телефона. Используйте формат +7XXXXXXXXXX")
            return
        
        await fsm_context.update_data(client_phone=client_phone)
        await fsm_context.set_state(CreateEventStates.waiting_for_description)
        
        await message.answer(
            "📝 <b>Введите описание события</b>\n\n"
            f"Телефон: {client_phone or 'Не указан'}\n"
            "Пример: Показ двухкомнатной квартиры, обсуждение условий\n"
            "Или нажмите /skip для пропуска",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки телефона клиента: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(CreateEventStates.waiting_for_description)
async def handle_event_description(message: Message, fsm_context: FSMContext):
    """Обработка описания события"""
    try:
        description = message.text.strip() if message.text != "/skip" else None
        
        await fsm_context.update_data(description=description)
        await fsm_context.set_state(CreateEventStates.waiting_for_confirmation)
        
        # Показ сводки для подтверждения
        data = await fsm_context.get_data()
        summary = _format_event_summary(data)
        
        keyboard = get_event_actions_keyboard()
        
        await message.answer(
            f"📋 <b>Проверьте данные события:</b>\n\n{summary}\n\n"
            "Все верно?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки описания события: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(F.data == "confirm_event")
async def confirm_event_creation(callback: CallbackQuery, fsm_context: FSMContext):
    """Подтверждение создания события"""
    try:
        data = await fsm_context.get_data()
        
        async with get_db() as db:
            calendar_service = CalendarService(db)
            
            user = await db.get(User, callback.from_user.id)
            if not user:
                await callback.message.edit_text("❌ Пользователь не найден.")
                return
            
            # Создание события
            event = await calendar_service.create_event(
                user_id=user.id,
                event_type=EventType(data['event_type']),
                title=data['title'],
                description=data.get('description'),
                start_time=data['start_time'],
                end_time=data['end_time'],
                location=data.get('location'),
                client_name=data.get('client_name'),
                client_phone=data.get('client_phone')
            )
            
            await fsm_context.clear()
            
            # Форматирование события для отображения
            event_text = format_event(event)
            
            await callback.message.edit_text(
                f"✅ <b>Событие успешно создано!</b>\n\n{event_text}",
                parse_mode="HTML"
            )
        
    except EventValidationError as e:
        await callback.message.edit_text(f"❌ Ошибка валидации: {e}")
    except CalendarConflictError as e:
        await callback.message.edit_text(f"❌ Конфликт в календаре: {e}")
    except Exception as e:
        logger.error(f"Ошибка создания события: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при создании события.")


@router.callback_query(F.data == "cancel_event")
async def cancel_event_creation(callback: CallbackQuery, fsm_context: FSMContext):
    """Отмена создания события"""
    try:
        await fsm_context.clear()
        await callback.message.edit_text("❌ Создание события отменено.")
        
    except Exception as e:
        logger.error(f"Ошибка отмены создания события: {e}")


@router.message(Command("suggest_time"))
async def suggest_meeting_time(message: Message):
    """Предложение времени для встречи"""
    try:
        # Парсинг параметров из сообщения
        # Формат: /suggest_time 60 25.12.2024 26.12.2024
        parts = message.text.split()
        if len(parts) < 4:
            await message.answer(
                "📅 <b>Предложение времени для встречи</b>\n\n"
                "Использование: /suggest_time <длительность_мин> <дата_начала> <дата_окончания>\n"
                "Пример: /suggest_time 60 25.12.2024 26.12.2024",
                parse_mode="HTML"
            )
            return
        
        try:
            duration = int(parts[1])
            start_date = datetime.strptime(parts[2], "%d.%m.%Y").date()
            end_date = datetime.strptime(parts[3], "%d.%m.%Y").date()
        except (ValueError, IndexError):
            await message.answer("❌ Неверный формат параметров.")
            return
        
        async with get_db() as db:
            calendar_service = CalendarService(db)
            
            user = await db.get(User, message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            suggestions = await calendar_service.suggest_meeting_times(
                user_id=user.id,
                duration_minutes=duration,
                start_date=start_datetime,
                end_date=end_datetime
            )
            
            if not suggestions:
                await message.answer("❌ В указанный период нет свободного времени.")
                return
            
            # Форматирование предложений
            suggestions_text = "🕐 <b>Предложения времени для встречи:</b>\n\n"
            for i, suggestion in enumerate(suggestions[:5], 1):
                suggestions_text += format_time_slot(suggestion, i)
            
            keyboard = get_time_slots_keyboard(suggestions[:5])
            
            await message.answer(
                suggestions_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка предложения времени: {e}")
        await message.answer("❌ Произошла ошибка при поиске времени.")


@router.message(Command("stats"))
async def show_calendar_stats(message: Message):
    """Показать статистику календаря"""
    try:
        async with get_db() as db:
            calendar_service = CalendarService(db)
            
            user = await db.get(User, message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден.")
                return
            
            stats = await calendar_service.get_calendar_stats(user.id, days=30)
            
            stats_text = "📊 <b>Статистика календаря (за 30 дней):</b>\n\n"
            stats_text += f"📈 Всего событий: {stats['total_events']}\n"
            stats_text += f"✅ Завершено: {stats['completed_events']}\n"
            stats_text += f"❌ Отменено: {stats['cancelled_events']}\n"
            stats_text += f"📅 Предстоящих: {stats['upcoming_events']}\n"
            stats_text += f"⏱️ Средняя продолжительность: {stats['average_duration']:.0f} мин\n\n"
            
            stats_text += "📅 <b>По типам событий:</b>\n"
            for event_type, count in stats['events_by_type'].items():
                if count > 0:
                    icon = _get_event_type_icon(event_type)
                    stats_text += f"{icon} {event_type.title()}: {count}\n"
            
            await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики.")


def _format_event_summary(data: dict) -> str:
    """Форматирование сводки события"""
    summary = f"🎯 <b>{data['title']}</b>\n"
    summary += f"📅 Дата: {data['date'].strftime('%d.%m.%Y')}\n"
    summary += f"🕐 Время: {data['start_time'].strftime('%H:%M')} - {data['end_time'].strftime('%H:%M')}\n"
    summary += f"⏱️ Продолжительность: {data['duration']} мин\n"
    
    if data.get('location'):
        summary += f"📍 Место: {data['location']}\n"
    
    if data.get('client_name'):
        summary += f"👤 Клиент: {data['client_name']}\n"
    
    if data.get('client_phone'):
        summary += f"📞 Телефон: {data['client_phone']}\n"
    
    if data.get('description'):
        summary += f"📝 Описание: {data['description']}\n"
    
    return summary


def _get_event_type_icon(event_type: str) -> str:
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