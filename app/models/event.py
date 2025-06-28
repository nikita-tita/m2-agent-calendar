from sqlalchemy import BigInteger, String, Text, DateTime, Enum, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import enum

from app.database import Base


class EventType(str, enum.Enum):
    """Типы событий"""
    SHOWING = "showing"      # Показ недвижимости
    MEETING = "meeting"      # Встреча с клиентом
    DEAL = "deal"           # Сделка
    TASK = "task"           # Задача
    CALL = "call"           # Звонок
    OTHER = "other"         # Другое


class EventStatus(str, enum.Enum):
    """Статусы событий"""
    ACTIVE = "active"       # Активное
    COMPLETED = "completed" # Завершено
    CANCELLED = "cancelled" # Отменено
    POSTPONED = "postponed" # Отложено


class CreatedFrom(str, enum.Enum):
    """Источник создания события"""
    VOICE = "voice"         # Голосовое сообщение
    TEXT = "text"           # Текстовое сообщение
    IMAGE = "image"         # Изображение/скриншот
    MANUAL = "manual"       # Ручной ввод
    API = "api"            # API запрос


class Event(Base):
    """Модель события календаря"""
    
    __tablename__ = "events"
    
    # Основные поля
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    
    # Информация о событии
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Время события
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Местоположение
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Тип и статус
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.ACTIVE, nullable=False, index=True)
    
    # Напоминания
    reminders: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    is_reminder_sent: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    
    # AI метаданные
    created_from: Mapped[CreatedFrom] = mapped_column(Enum(CreatedFrom), nullable=False, index=True)
    original_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Связанные объекты
    # client_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("clients.id"), nullable=True, index=True)
    # property_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("properties.id"), nullable=True, index=True)
    
    # Дополнительные данные
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="events")
    # client: Mapped[Optional["Client"]] = relationship("Client", back_populates="events")
    # property_obj: Mapped[Optional["Property"]] = relationship("Property", back_populates="events")
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', type={self.event_type.value})>"
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Длительность события в минутах"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_all_day(self) -> bool:
        """Является ли событие на весь день"""
        if not self.end_time:
            return False
        delta = self.end_time - self.start_time
        return delta.total_seconds() >= 24 * 60 * 60
    
    def add_reminder(self, minutes_before: int, message: str = None) -> None:
        """Добавить напоминание"""
        reminder = {
            "minutes_before": minutes_before,
            "message": message or f"Напоминание: {self.title}",
            "sent": False
        }
        self.reminders.append(reminder)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Получить метаданные события"""
        return self.event_metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Установить метаданные события"""
        self.event_metadata[key] = value 