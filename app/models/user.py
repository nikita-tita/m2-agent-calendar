from sqlalchemy import BigInteger, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Telegram данные
    telegram_id = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username = mapped_column(String(100))
    first_name = mapped_column(String(100))
    last_name = mapped_column(String(100))
    
    # Контактная информация
    email = mapped_column(String(255))
    phone = mapped_column(String(50))
    
    # Статус и настройки
    is_active = mapped_column(Boolean, default=True)
    is_admin = mapped_column(Boolean, default=False)
    is_verified = mapped_column(Boolean, default=False)
    
    # Настройки уведомлений
    enable_notifications = mapped_column(Boolean, default=True)
    notification_language = mapped_column(String(10), default="ru")
    reminder_enabled = mapped_column(Boolean, default=True)
    daily_digest_enabled = mapped_column(Boolean, default=True)
    
    # Настройки
    timezone = mapped_column(String(50), default="Europe/Moscow", nullable=False)
    settings = mapped_column(JSON, default=dict, nullable=False)
    preferences = mapped_column(JSON, default=dict, nullable=False)
    
    # Метаданные
    created_at = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    last_activity = mapped_column(DateTime(timezone=True), default=func.now())
    
    # Отношения
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    # clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    # properties = relationship("Property", back_populates="user", cascade="all, delete-orphan")
    # ai_data = relationship("AIData", back_populates="user", cascade="all, delete-orphan")
    # calendar_events = relationship("CalendarEvent", back_populates="user")
    # calendar_settings = relationship("CalendarSettings", back_populates="user", uselist=False)
    # event_templates = relationship("EventTemplate", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"Пользователь {self.telegram_id}"
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя"""
        if self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"Пользователь {self.telegram_id}"
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получить настройку пользователя"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Установить настройку пользователя"""
        self.settings[key] = value
    
    def update_activity(self):
        """Обновление времени последней активности"""
        self.last_activity = func.now()
    
    def is_online(self, minutes: int = 5) -> bool:
        """Проверка, активен ли пользователь"""
        if not self.last_activity:
            return False
        
        time_diff = func.now() - self.last_activity
        return time_diff.total_seconds() < minutes * 60 