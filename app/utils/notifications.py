"""
Сервис уведомлений для календаря
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import pytz
import smtplib
from email.mime.text import MIMEText

from app.models.calendar import CalendarEvent, EventReminder
from app.config import settings
from app.utils.telegram import TelegramBot
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    """Сообщение уведомления"""
    title: str
    body: str
    priority: str = "normal"  # low, normal, high, urgent
    channels: List[str] = None  # telegram, email, sms


class NotificationService:
    """Сервис управления уведомлениями"""
    
    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        
    async def send_event_created_notification(self, event: CalendarEvent):
        """Отправка уведомления о создании события"""
        try:
            message = self._format_event_created_message(event)
            
            # Отправка в Telegram
            if event.user.telegram_id:
                await self.telegram_bot.send_message(
                    chat_id=event.user.telegram_id,
                    text=message.body,
                    parse_mode="HTML"
                )
            
            # Отправка email (если настроен)
            if event.user.email and event.user.calendar_settings.enable_email_notifications:
                await self._send_email_notification(event.user.email, message)
            
            logger.info(f"Отправлено уведомление о создании события {event.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о создании события: {e}")
    
    async def send_event_updated_notification(self, event: CalendarEvent):
        """Отправка уведомления об изменении события"""
        try:
            message = self._format_event_updated_message(event)
            
            if event.user.telegram_id:
                await self.telegram_bot.send_message(
                    chat_id=event.user.telegram_id,
                    text=message.body,
                    parse_mode="HTML"
                )
            
            logger.info(f"Отправлено уведомление об изменении события {event.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об изменении события: {e}")
    
    async def send_event_reminder(self, event: CalendarEvent):
        """Отправка напоминания о событии"""
        try:
            message = self._format_event_reminder_message(event)
            
            if event.user.telegram_id:
                await self.telegram_bot.send_message(
                    chat_id=event.user.telegram_id,
                    text=message.body,
                    parse_mode="HTML"
                )
            
            # Отметка о отправке напоминания
            event.reminder_sent = True
            event.reminder_time = datetime.utcnow()
            
            logger.info(f"Отправлено напоминание о событии {event.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания: {e}")
    
    async def send_event_cancelled_notification(self, event: CalendarEvent):
        """Отправка уведомления об отмене события"""
        try:
            message = self._format_event_cancelled_message(event)
            
            if event.user.telegram_id:
                await self.telegram_bot.send_message(
                    chat_id=event.user.telegram_id,
                    text=message.body,
                    parse_mode="HTML"
                )
            
            logger.info(f"Отправлено уведомление об отмене события {event.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об отмене события: {e}")
    
    async def send_daily_schedule(self, user_id: int, events: List[CalendarEvent]):
        """Отправка ежедневного расписания"""
        try:
            if not events:
                return
            
            message = self._format_daily_schedule_message(events)
            
            # Получение пользователя
            user = events[0].user
            if user.telegram_id:
                await self.telegram_bot.send_message(
                    chat_id=user.telegram_id,
                    text=message.body,
                    parse_mode="HTML"
                )
            
            logger.info(f"Отправлено ежедневное расписание пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного расписания: {e}")
    
    async def send_weekly_summary(self, user_id: int, stats: Dict[str, Any]):
        """Отправка еженедельной сводки"""
        try:
            message = self._format_weekly_summary_message(stats)
            
            # Получение пользователя (нужно передать в параметрах)
            # user = await get_user_by_id(user_id)
            # if user.telegram_id:
            #     await self.telegram_bot.send_message(
            #         chat_id=user.telegram_id,
            #         text=message.body,
            #         parse_mode="HTML"
            #     )
            
            logger.info(f"Отправлена еженедельная сводка пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки еженедельной сводки: {e}")
    
    async def schedule_reminder(self, event: CalendarEvent, reminder_time: datetime):
        """Планирование напоминания"""
        try:
            # Создание записи напоминания
            reminder = EventReminder(
                event_id=event.id,
                reminder_time=reminder_time,
                reminder_type="notification"
            )
            
            # Здесь можно добавить логику планирования через Celery или другой планировщик
            # await schedule_task("send_reminder", reminder.id, eta=reminder_time)
            
            logger.info(f"Запланировано напоминание для события {event.id} на {reminder_time}")
            
        except Exception as e:
            logger.error(f"Ошибка планирования напоминания: {e}")
    
    async def send_availability_notification(self, user_id: int, available_slots: List[Dict]):
        """Отправка уведомления о доступных слотах"""
        try:
            message = self._format_availability_message(available_slots)
            
            # Получение пользователя (нужно передать в параметрах)
            # user = await get_user_by_id(user_id)
            # if user.telegram_id:
            #     await self.telegram_bot.send_message(
            #         chat_id=user.telegram_id,
            #         text=message.body,
            #         parse_mode="HTML"
            #     )
            
            logger.info(f"Отправлено уведомление о доступных слотах пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о доступных слотах: {e}")
    
    def _format_event_created_message(self, event: CalendarEvent) -> NotificationMessage:
        """Форматирование сообщения о создании события"""
        title = "📅 Новое событие создано"
        
        body = f"""
<b>{title}</b>

🎯 <b>{event.title}</b>
📅 Дата: {event.start_time.strftime('%d.%m.%Y')}
🕐 Время: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}
📍 Место: {event.location or 'Не указано'}
👤 Клиент: {event.client_name or 'Не указан'}

{event.description or ''}
        """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="normal",
            channels=["telegram"]
        )
    
    def _format_event_updated_message(self, event: CalendarEvent) -> NotificationMessage:
        """Форматирование сообщения об изменении события"""
        title = "✏️ Событие изменено"
        
        body = f"""
<b>{title}</b>

🎯 <b>{event.title}</b>
📅 Дата: {event.start_time.strftime('%d.%m.%Y')}
🕐 Время: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}
📍 Место: {event.location or 'Не указано'}
👤 Клиент: {event.client_name or 'Не указан'}

{event.description or ''}
        """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="normal",
            channels=["telegram"]
        )
    
    def _format_event_reminder_message(self, event: CalendarEvent) -> NotificationMessage:
        """Форматирование сообщения напоминания"""
        title = "⏰ Напоминание о событии"
        
        # Расчет времени до события
        time_until = event.start_time - datetime.now(self.moscow_tz)
        minutes_until = int(time_until.total_seconds() / 60)
        
        if minutes_until <= 0:
            time_text = "Событие начинается сейчас!"
        elif minutes_until < 60:
            time_text = f"Через {minutes_until} минут"
        else:
            hours = minutes_until // 60
            minutes = minutes_until % 60
            time_text = f"Через {hours}ч {minutes}м"
        
        body = f"""
<b>{title}</b>

🎯 <b>{event.title}</b>
⏰ {time_text}
📅 Дата: {event.start_time.strftime('%d.%m.%Y')}
🕐 Время: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}
📍 Место: {event.location or 'Не указано'}
👤 Клиент: {event.client_name or 'Не указан'}

{event.description or ''}
        """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="high",
            channels=["telegram"]
        )
    
    def _format_event_cancelled_message(self, event: CalendarEvent) -> NotificationMessage:
        """Форматирование сообщения об отмене события"""
        title = "❌ Событие отменено"
        
        body = f"""
<b>{title}</b>

🎯 <b>{event.title}</b>
📅 Дата: {event.start_time.strftime('%d.%m.%Y')}
🕐 Время: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}
👤 Клиент: {event.client_name or 'Не указан'}

{event.notes or ''}
        """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="normal",
            channels=["telegram"]
        )
    
    def _format_daily_schedule_message(self, events: List[CalendarEvent]) -> NotificationMessage:
        """Форматирование ежедневного расписания"""
        title = "📅 Расписание на сегодня"
        
        if not events:
            body = f"""
<b>{title}</b>

✅ Сегодня у вас нет запланированных событий.
            """.strip()
        else:
            events_text = ""
            for i, event in enumerate(events, 1):
                events_text += f"""
{i}. <b>{event.title}</b>
   🕐 {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}
   📍 {event.location or 'Место не указано'}
   👤 {event.client_name or 'Клиент не указан'}
                """.strip() + "\n\n"
            
            body = f"""
<b>{title}</b>

{events_text.strip()}
            """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="normal",
            channels=["telegram"]
        )
    
    def _format_weekly_summary_message(self, stats: Dict[str, Any]) -> NotificationMessage:
        """Форматирование еженедельной сводки"""
        title = "📊 Еженедельная сводка"
        
        body = f"""
<b>{title}</b>

📈 <b>Статистика за неделю:</b>
• Всего событий: {stats['total_events']}
• Завершено: {stats['completed_events']}
• Отменено: {stats['cancelled_events']}
• Предстоящих: {stats['upcoming_events']}

📅 <b>По типам событий:</b>
{self._format_events_by_type(stats.get('events_by_type', {}))}

⏱️ Средняя продолжительность: {stats.get('average_duration', 0):.0f} мин
        """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="low",
            channels=["telegram"]
        )
    
    def _format_availability_message(self, available_slots: List[Dict]) -> NotificationMessage:
        """Форматирование сообщения о доступных слотах"""
        title = "🕐 Доступные слоты времени"
        
        if not available_slots:
            body = f"""
<b>{title}</b>

❌ К сожалению, в указанный период нет свободного времени.
            """.strip()
        else:
            slots_text = ""
            for i, slot in enumerate(available_slots[:5], 1):  # Показываем только первые 5
                start_time = slot['start_time'].strftime('%H:%M')
                end_time = slot['end_time'].strftime('%H:%M')
                confidence = slot.get('confidence', 0)
                
                slots_text += f"""
{i}. {start_time} - {end_time} ({confidence:.0%} уверенность)
                """.strip() + "\n"
            
            body = f"""
<b>{title}</b>

{slots_text.strip()}

💡 Выберите удобное время для встречи.
            """.strip()
        
        return NotificationMessage(
            title=title,
            body=body,
            priority="normal",
            channels=["telegram"]
        )
    
    def _format_events_by_type(self, events_by_type: Dict[str, int]) -> str:
        """Форматирование событий по типам"""
        if not events_by_type:
            return "Нет данных"
        
        result = ""
        type_icons = {
            "meeting": "🤝",
            "showing": "🏠",
            "call": "📞",
            "consultation": "💼",
            "contract": "📋",
            "other": "📝"
        }
        
        for event_type, count in events_by_type.items():
            icon = type_icons.get(event_type, "📝")
            result += f"• {icon} {event_type.title()}: {count}\n"
        
        return result.strip()
    
    async def _send_email_notification(self, email: str, message: NotificationMessage):
        """Отправка email уведомления"""
        try:
            # Здесь должна быть интеграция с email сервисом
            # Например, через SMTP или внешний API
            logger.info(f"Email уведомление отправлено на {email}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки email уведомления: {e}")
    
    async def _send_sms_notification(self, phone: str, message: NotificationMessage):
        """Отправка SMS уведомления"""
        try:
            # Здесь должна быть интеграция с SMS сервисом
            logger.info(f"SMS уведомление отправлено на {phone}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки SMS уведомления: {e}") 