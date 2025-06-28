"""
Схемы для работы с событиями календаря
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class EventType(str, Enum):
    """Типы событий"""
    MEETING = "meeting"
    SHOWING = "showing"
    CALL = "call"
    TASK = "task"
    REMINDER = "reminder"
    OTHER = "other"


class EventStatus(str, Enum):
    """Статусы событий"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class EventBase(BaseModel):
    """Базовая схема события"""
    title: str = Field(..., min_length=1, max_length=200, description="Название события")
    description: Optional[str] = Field(None, max_length=1000, description="Описание события")
    start_time: datetime = Field(..., description="Время начала события")
    end_time: datetime = Field(..., description="Время окончания события")
    event_type: EventType = Field(..., description="Тип события")
    location: Optional[str] = Field(None, max_length=200, description="Место проведения")
    notes: Optional[str] = Field(None, max_length=1000, description="Дополнительные заметки")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class EventCreate(EventBase):
    """Схема для создания события"""
    property_id: Optional[int] = Field(None, description="ID объекта недвижимости")
    client_name: Optional[str] = Field(None, max_length=100, description="Имя клиента")
    client_phone: Optional[str] = Field(None, max_length=20, description="Телефон клиента")


class EventUpdate(BaseModel):
    """Схема для обновления события"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)
    property_id: Optional[int] = None
    client_name: Optional[str] = Field(None, max_length=100)
    client_phone: Optional[str] = Field(None, max_length=20)


class EventResponse(EventBase):
    """Схема для ответа с событием"""
    id: int
    user_id: int
    status: EventStatus
    property_id: Optional[int] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    external_event_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Схема для списка событий"""
    events: List[EventResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class EventFilter(BaseModel):
    """Схема для фильтрации событий"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    property_id: Optional[int] = None
    client_name: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100) 