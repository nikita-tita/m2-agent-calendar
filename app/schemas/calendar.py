"""
Pydantic схемы для календаря и событий
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
from dataclasses import dataclass

from app.models.calendar import EventType, EventStatus

@dataclass
class EventSlot:
    """Слот времени для события"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    is_available: bool = True

@dataclass
class EventSuggestion:
    """Предложение времени для встречи"""
    start_time: datetime
    end_time: datetime
    confidence: float
    reason: str

class EventCreate(BaseModel):
    """Схема для создания события"""
    title: str = Field(..., min_length=1, max_length=200, description="Название события")
    description: Optional[str] = Field(None, max_length=2000, description="Описание события")
    event_type: EventType = Field(..., description="Тип события")
    start_time: datetime = Field(..., description="Время начала")
    end_time: datetime = Field(..., description="Время окончания")
    location: Optional[str] = Field(None, max_length=500, description="Место проведения")
    client_name: Optional[str] = Field(None, max_length=100, description="Имя клиента")
    client_phone: Optional[str] = Field(None, max_length=20, description="Телефон клиента")
    client_email: Optional[str] = Field(None, max_length=100, description="Email клиента")
    property_id: Optional[int] = Field(None, description="ID объекта недвижимости")
    reminder_time: Optional[datetime] = Field(None, description="Время напоминания")
    notes: Optional[str] = Field(None, max_length=1000, description="Заметки")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v
    
    @validator('reminder_time')
    def validate_reminder_time(cls, v, values):
        if v and 'start_time' in values and v >= values['start_time']:
            raise ValueError('Время напоминания должно быть раньше времени начала')
        return v


class EventUpdate(BaseModel):
    """Схема для обновления события"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    client_name: Optional[str] = Field(None, max_length=100)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = Field(None, max_length=100)
    property_id: Optional[int] = None
    reminder_time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[EventStatus] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and values.get('start_time') and v <= values['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v
    
    @validator('reminder_time')
    def validate_reminder_time(cls, v, values):
        if v and values.get('start_time') and v >= values['start_time']:
            raise ValueError('Время напоминания должно быть раньше времени начала')
        return v


class EventResponse(BaseModel):
    """Схема для ответа с событием"""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    event_type: EventType
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    client_name: Optional[str]
    client_phone: Optional[str]
    client_email: Optional[str]
    property_id: Optional[int]
    reminder_time: Optional[datetime]
    notes: Optional[str]
    status: EventStatus
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
    
    @property
    def duration_minutes(self) -> int:
        """Продолжительность события в минутах"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    @property
    def is_overdue(self) -> bool:
        """Проверка, завершилось ли событие"""
        return datetime.now() > self.end_time
    
    @property
    def is_upcoming(self) -> bool:
        """Проверка, предстоит ли событие"""
        return datetime.now() < self.start_time


class EventListResponse(BaseModel):
    """Схема для ответа со списком событий"""
    events: List[EventResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class EventFilter(BaseModel):
    """Схема для фильтрации событий"""
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    client_name: Optional[str] = None
    property_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('Дата окончания не может быть раньше даты начала')
        return v


class EventConflict(BaseModel):
    """Схема для конфликта событий"""
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    
    class Config:
        from_attributes = True


class EventStatistics(BaseModel):
    """Схема для статистики событий"""
    total_events: int
    completed_events: int
    cancelled_events: int
    upcoming_events: int
    overdue_events: int
    events_by_type: dict
    events_by_status: dict
    average_duration: float
    busy_hours: dict
    
    class Config:
        from_attributes = True


class TimeSlot(BaseModel):
    """Схема для временного слота"""
    start_time: datetime
    end_time: datetime
    is_available: bool
    conflicting_event: Optional[EventConflict] = None
    
    class Config:
        from_attributes = True


class EventSuggestion(BaseModel):
    """Схема для предложения времени события"""
    suggested_time: datetime
    duration: int  # в минутах
    confidence: float  # от 0 до 1
    reason: str
    
    class Config:
        from_attributes = True


class CalendarExport(BaseModel):
    """Схема для экспорта календаря"""
    format: str = Field(..., pattern="^(ics|json|csv)$")
    start_date: datetime
    end_date: datetime
    include_past_events: bool = True
    include_cancelled: bool = False
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Дата окончания должна быть позже даты начала')
        return v


class CalendarImport(BaseModel):
    """Схема для импорта календаря"""
    file_url: str = Field(..., description="URL файла для импорта")
    format: str = Field(..., pattern="^(ics|json|csv)$")
    update_existing: bool = False
    skip_duplicates: bool = True


class RecurringEventCreate(BaseModel):
    """Схема для создания повторяющегося события"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: EventType
    start_time: datetime
    end_time: datetime
    location: Optional[str] = Field(None, max_length=500)
    client_name: Optional[str] = Field(None, max_length=100)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = Field(None, max_length=100)
    property_id: Optional[int] = None
    reminder_time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    # Параметры повторения
    recurrence_type: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    recurrence_interval: int = Field(1, ge=1, le=52)
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = Field(None, ge=1, le=100)
    weekdays: Optional[List[int]] = Field(None, description="Дни недели (0-6, где 0 - понедельник)")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v
    
    @validator('recurrence_end_date')
    def validate_recurrence_end_date(cls, v, values):
        if v and 'start_time' in values and v <= values['start_time']:
            raise ValueError('Дата окончания повторения должна быть позже времени начала')
        return v
    
    @validator('weekdays')
    def validate_weekdays(cls, v):
        if v:
            for day in v:
                if day < 0 or day > 6:
                    raise ValueError('Дни недели должны быть от 0 до 6')
        return v


class EventTemplate(BaseModel):
    """Схема для шаблона события"""
    id: int
    name: str
    title_template: str
    description_template: Optional[str]
    event_type: EventType
    default_duration: int  # в минутах
    location_template: Optional[str]
    notes_template: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventTemplateCreate(BaseModel):
    """Схема для создания шаблона события"""
    name: str = Field(..., min_length=1, max_length=100)
    title_template: str = Field(..., min_length=1, max_length=200)
    description_template: Optional[str] = Field(None, max_length=2000)
    event_type: EventType
    default_duration: int = Field(30, ge=15, le=480)  # от 15 минут до 8 часов
    location_template: Optional[str] = Field(None, max_length=500)
    notes_template: Optional[str] = Field(None, max_length=1000)


class EventTemplateUpdate(BaseModel):
    """Схема для обновления шаблона события"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title_template: Optional[str] = Field(None, min_length=1, max_length=200)
    description_template: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[EventType] = None
    default_duration: Optional[int] = Field(None, ge=15, le=480)
    location_template: Optional[str] = Field(None, max_length=500)
    notes_template: Optional[str] = Field(None, max_length=1000)


class CalendarSettings(BaseModel):
    """Схема для настроек календаря"""
    work_start_time: str = Field("09:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    work_end_time: str = Field("18:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    work_days: List[int] = Field([0, 1, 2, 3, 4], description="Дни недели (0-6)")
    default_event_duration: int = Field(60, ge=15, le=480)
    reminder_default: int = Field(15, ge=0, le=1440)  # в минутах
    timezone: str = Field("Europe/Moscow")
    auto_check_conflicts: bool = True
    allow_overlapping: bool = False
    
    @validator('work_end_time')
    def validate_work_end_time(cls, v, values):
        if 'work_start_time' in values and v <= values['work_start_time']:
            raise ValueError('Время окончания работы должно быть позже времени начала')
        return v
    
    @validator('work_days')
    def validate_work_days(cls, v):
        for day in v:
            if day < 0 or day > 6:
                raise ValueError('Дни недели должны быть от 0 до 6')
        return list(set(v))  # Убираем дубликаты


class NotificationSettings(BaseModel):
    """Схема для настроек уведомлений"""
    email_notifications: bool = True
    telegram_notifications: bool = True
    sms_notifications: bool = False
    reminder_before_event: int = Field(15, ge=0, le=1440)  # в минутах
    daily_summary: bool = True
    weekly_summary: bool = True
    conflict_notifications: bool = True
    client_notifications: bool = False
    
    class Config:
        from_attributes = True


class CalendarIntegration(BaseModel):
    """Схема для интеграции с внешними календарями"""
    google_calendar_enabled: bool = False
    google_calendar_id: Optional[str] = None
    outlook_calendar_enabled: bool = False
    outlook_calendar_id: Optional[str] = None
    sync_direction: str = Field("both", pattern="^(import|export|both)$")
    auto_sync: bool = True
    sync_interval: int = Field(30, ge=5, le=1440)  # в минутах
    
    class Config:
        from_attributes = True 