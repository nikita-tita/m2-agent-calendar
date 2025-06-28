"""
Модели календаря и событий
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class EventType(str, Enum):
    """Типы событий"""
    MEETING = "meeting"  # Встреча с клиентом
    SHOWING = "showing"  # Показ недвижимости
    CALL = "call"  # Звонок
    CONSULTATION = "consultation"  # Консультация
    CONTRACT = "contract"  # Подписание договора
    OTHER = "other"  # Другое


class EventStatus(str, Enum):
    """Статусы событий"""
    SCHEDULED = "scheduled"  # Запланировано
    IN_PROGRESS = "in_progress"  # В процессе
    COMPLETED = "completed"  # Завершено
    CANCELLED = "cancelled"  # Отменено
    RESCHEDULED = "rescheduled"  # Перенесено


class CalendarEvent(Base):
    """Модель события календаря"""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Основная информация
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Время
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    
    # Статус
    status = Column(String, default=EventStatus.SCHEDULED, index=True)
    
    # Связанная недвижимость
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    
    # Информация о клиенте
    client_name = Column(String(255))
    client_phone = Column(String(50))
    
    # Место проведения
    location = Column(String(500))
    
    # Дополнительная информация
    notes = Column(Text)
    
    # Внешний календарь
    external_event_id = Column(String(255))  # ID события во внешнем календаре
    external_calendar_type = Column(String(50))  # Тип внешнего календаря (Google, Outlook, etc.)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Настройки уведомлений
    reminder_sent = Column(Boolean, default=False)
    reminder_time = Column(DateTime)  # Время отправки напоминания
    
    # Связи
    user = relationship("User", back_populates="calendar_events")
    property_obj = relationship("Property", back_populates="calendar_events")
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start_time={self.start_time})>"
    
    @property
    def duration_minutes(self) -> int:
        """Продолжительность события в минутах"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0
    
    @property
    def is_overdue(self) -> bool:
        """Проверка, прошло ли время события"""
        return datetime.utcnow() > self.end_time
    
    @property
    def is_today(self) -> bool:
        """Проверка, происходит ли событие сегодня"""
        today = datetime.utcnow().date()
        return self.start_time.date() == today


class EventReminder(Base):
    """Модель напоминаний о событиях"""
    __tablename__ = "event_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Связь с событием
    event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=False)
    
    # Время напоминания
    reminder_time = Column(DateTime, nullable=False, index=True)
    
    # Тип напоминания
    reminder_type = Column(String(50), default="notification")  # notification, email, sms
    
    # Статус
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    event = relationship("CalendarEvent")
    
    def __repr__(self):
        return f"<EventReminder(id={self.id}, event_id={self.event_id}, reminder_time={self.reminder_time})>"


class CalendarSettings(Base):
    """Настройки календаря пользователя"""
    __tablename__ = "calendar_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Пользователь
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Рабочие часы
    work_start_time = Column(String(10), default="09:00")  # HH:MM
    work_end_time = Column(String(10), default="18:00")  # HH:MM
    
    # Рабочие дни (битовая маска: 1=Пн, 2=Вт, 4=Ср, 8=Чт, 16=Пт, 32=Сб, 64=Вс)
    work_days = Column(Integer, default=31)  # Пн-Пт по умолчанию
    
    # Настройки уведомлений
    default_reminder_minutes = Column(Integer, default=60)  # За сколько минут напоминать
    enable_email_notifications = Column(Boolean, default=True)
    enable_telegram_notifications = Column(Boolean, default=True)
    enable_sms_notifications = Column(Boolean, default=False)
    
    # Интеграция с внешними календарями
    google_calendar_enabled = Column(Boolean, default=False)
    google_calendar_id = Column(String(255))
    outlook_calendar_enabled = Column(Boolean, default=False)
    outlook_calendar_id = Column(String(255))
    
    # Автоматическое планирование
    auto_schedule_enabled = Column(Boolean, default=True)
    min_meeting_duration = Column(Integer, default=30)  # Минимальная продолжительность встречи
    max_meeting_duration = Column(Integer, default=120)  # Максимальная продолжительность встречи
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="calendar_settings")
    
    def __repr__(self):
        return f"<CalendarSettings(user_id={self.user_id})>"
    
    def is_work_day(self, date: datetime) -> bool:
        """Проверка, является ли день рабочим"""
        day_mask = 1 << date.weekday()
        return bool(self.work_days & day_mask)
    
    def is_work_time(self, time: datetime) -> bool:
        """Проверка, является ли время рабочим"""
        time_str = time.strftime("%H:%M")
        return self.work_start_time <= time_str <= self.work_end_time


class EventTemplate(Base):
    """Шаблоны событий для быстрого создания"""
    __tablename__ = "event_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Пользователь
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Информация о шаблоне
    name = Column(String(255), nullable=False)
    event_type = Column(String, nullable=False)
    title_template = Column(String(255), nullable=False)
    description_template = Column(Text)
    
    # Длительность по умолчанию (в минутах)
    default_duration = Column(Integer, default=60)
    
    # Место по умолчанию
    default_location = Column(String(500))
    
    # Настройки напоминаний
    reminder_minutes = Column(Integer, default=60)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="event_templates")
    
    def __repr__(self):
        return f"<EventTemplate(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def format_title(self, **kwargs) -> str:
        """Форматирование заголовка с подстановкой переменных"""
        return self.title_template.format(**kwargs)
    
    def format_description(self, **kwargs) -> str:
        """Форматирование описания с подстановкой переменных"""
        if self.description_template:
            return self.description_template.format(**kwargs)
        return "" 