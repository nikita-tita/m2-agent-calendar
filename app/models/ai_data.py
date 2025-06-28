from sqlalchemy import BigInteger, String, Text, DateTime, Float, Integer, Boolean, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from app.database import Base


class AIProcessingType(str, enum.Enum):
    """Типы AI обработки"""
    SPEECH_TO_TEXT = "speech_to_text"      # Распознавание речи
    TEXT_ANALYSIS = "text_analysis"        # Анализ текста
    IMAGE_OCR = "image_ocr"               # OCR изображений
    INTENT_CLASSIFICATION = "intent_classification"  # Классификация намерений
    ENTITY_EXTRACTION = "entity_extraction"  # Извлечение сущностей
    ROUTE_OPTIMIZATION = "route_optimization"  # Оптимизация маршрутов


class AIProvider(str, enum.Enum):
    """Провайдеры AI сервисов"""
    OPENAI = "openai"
    YANDEX = "yandex"
    LOCAL = "local"
    EASYOCR = "easyocr"
    WHISPER = "whisper"


class AIData(Base):
    """Модель для хранения AI метаданных"""
    
    __tablename__ = "ai_data"
    
    # Основные поля
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    
    # Связанные объекты
    event_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=True, index=True)
    client_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("clients.id"), nullable=True, index=True)
    property_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("properties.id"), nullable=True, index=True)
    
    # Тип обработки
    processing_type: Mapped[AIProcessingType] = mapped_column(Enum(AIProcessingType), nullable=False, index=True)
    provider: Mapped[AIProvider] = mapped_column(Enum(AIProvider), nullable=False, index=True)
    
    # Исходные данные
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Входные данные
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Результат обработки
    
    # Метаданные обработки
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Уверенность
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Время обработки в секундах
    tokens_used: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # Использованные токены
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Стоимость обработки
    
    # Статус
    is_success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Дополнительные данные
    ai_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="ai_data")
    event: Mapped[Optional["Event"]] = relationship("Event")
    client: Mapped[Optional["Client"]] = relationship("Client")
    property_obj: Mapped[Optional["Property"]] = relationship("Property")
    
    def __repr__(self) -> str:
        return f"<AIData(id={self.id}, type={self.processing_type.value}, provider={self.provider.value})>"
    
    def get_input(self, key: str, default: Any = None) -> Any:
        """Получить входные данные"""
        return self.input_data.get(key, default)
    
    def set_input(self, key: str, value: Any) -> None:
        """Установить входные данные"""
        self.input_data[key] = value
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Получить выходные данные"""
        return self.output_data.get(key, default)
    
    def set_output(self, key: str, value: Any) -> None:
        """Установить выходные данные"""
        self.output_data[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Получить метаданные"""
        return self.ai_metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Установить метаданные"""
        self.ai_metadata[key] = value
    
    @property
    def processing_cost_rub(self) -> Optional[float]:
        """Стоимость обработки в рублях"""
        if self.cost is not None:
            # Примерный курс (можно вынести в настройки)
            return self.cost * 100  # Примерный курс USD/RUB
        return None 