"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator, computed_field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # =============================================================================
    # НАСТРОЙКИ ПРИЛОЖЕНИЯ
    # =============================================================================
    
    # Окружение
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Секретный ключ
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    # =============================================================================
    # БАЗА ДАННЫХ
    # =============================================================================
    
    # PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/realestate_bot",
        env="DATABASE_URL"
    )
    
    # Настройки пула соединений
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Настройки Redis для кэширования
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # =============================================================================
    # TELEGRAM BOT
    # =============================================================================
    
    # Токен бота
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    
    # ID администратора (опционально)
    ADMIN_TELEGRAM_ID: Optional[int] = Field(default=None, env="ADMIN_TELEGRAM_ID")
    
    # =============================================================================
    # AI СЕРВИСЫ
    # =============================================================================
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Yandex SpeechKit
    YANDEX_SPEECHKIT_API_KEY: Optional[str] = Field(default=None, env="YANDEX_SPEECHKIT_API_KEY")
    
    # Yandex Maps
    YANDEX_MAPS_API_KEY: Optional[str] = Field(default=None, env="YANDEX_MAPS_API_KEY")
    
    # =============================================================================
    # НАСТРОЙКИ ЛОГИРОВАНИЯ
    # =============================================================================
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Telegram для логов (опционально)
    LOG_TELEGRAM_CHAT_ID: Optional[int] = Field(default=None, env="LOG_TELEGRAM_CHAT_ID")
    
    # =============================================================================
    # НАСТРОЙКИ ФАЙЛОВ
    # =============================================================================
    
    # Путь для временных файлов
    TEMP_DIR: str = Field(default="./temp", env="TEMP_DIR")
    
    # Максимальный размер файла (в байтах)
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # =============================================================================
    # НАСТРОЙКИ КАЛЕНДАРЯ
    # =============================================================================
    
    # Временная зона по умолчанию
    DEFAULT_TIMEZONE: str = Field(default="Europe/Moscow", env="DEFAULT_TIMEZONE")
    
    # Интервал напоминаний (в минутах)
    REMINDER_INTERVALS: List[int] = Field(default=[15, 30, 60, 1440])
    
    # =============================================================================
    # НАСТРОЙКИ БЕЗОПАСНОСТИ
    # =============================================================================
    
    # Время жизни JWT токена (в минутах)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Максимальное количество попыток входа
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    
    # Блокировка после неудачных попыток (в минутах)
    LOGIN_BLOCK_DURATION: int = Field(default=15, env="LOGIN_BLOCK_DURATION")
    
    # Настройки шифрования
    ENCRYPTION_KEY: str = Field(default="", env="ENCRYPTION_KEY")
    
    # Настройки паролей
    MIN_PASSWORD_LENGTH: int = Field(default=8, env="MIN_PASSWORD_LENGTH")
    REQUIRE_SPECIAL_CHARS: bool = Field(default=True, env="REQUIRE_SPECIAL_CHARS")
    
    # =============================================================================
    # НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ
    # =============================================================================
    
    # Количество воркеров для FastAPI
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # Количество воркеров для Celery
    CELERY_WORKERS: int = Field(default=2, env="CELERY_WORKERS")
    
    # Таймаут для AI запросов (в секундах)
    AI_REQUEST_TIMEOUT: int = Field(default=30, env="AI_REQUEST_TIMEOUT")
    
    # =============================================================================
    # НАСТРОЙКИ КЭШИРОВАНИЯ
    # =============================================================================
    
    # Время жизни кэша (в секундах)
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    
    # Время жизни кэша геокодирования (в секундах)
    GEOCODE_CACHE_TTL: int = Field(default=86400, env="GEOCODE_CACHE_TTL")  # 24 часа
    
    # Настройки кэша для различных типов данных
    USER_CACHE_TTL: int = Field(default=1800, env="USER_CACHE_TTL")  # 30 минут
    PROPERTY_CACHE_TTL: int = Field(default=3600, env="PROPERTY_CACHE_TTL")  # 1 час
    CALENDAR_CACHE_TTL: int = Field(default=900, env="CALENDAR_CACHE_TTL")  # 15 минут
    ANALYTICS_CACHE_TTL: int = Field(default=7200, env="ANALYTICS_CACHE_TTL")  # 2 часа
    
    # =============================================================================
    # НАСТРОЙКИ ОГРАНИЧЕНИЯ СКОРОСТИ
    # =============================================================================
    
    # Лимиты запросов
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 час
    
    # Лимиты для API
    API_RATE_LIMIT_REQUESTS: int = Field(default=1000, env="API_RATE_LIMIT_REQUESTS")
    API_RATE_LIMIT_WINDOW: int = Field(default=3600, env="API_RATE_LIMIT_WINDOW")
    
    # Лимиты для AI запросов
    AI_RATE_LIMIT_REQUESTS: int = Field(default=50, env="AI_RATE_LIMIT_REQUESTS")
    AI_RATE_LIMIT_WINDOW: int = Field(default=3600, env="AI_RATE_LIMIT_WINDOW")
    
    # =============================================================================
    # НАСТРОЙКИ ОПТИМИЗАЦИИ БАЗЫ ДАННЫХ
    # =============================================================================
    
    # Автоматическая очистка старых данных
    AUTO_CLEANUP_ENABLED: bool = Field(default=True, env="AUTO_CLEANUP_ENABLED")
    
    # Время хранения данных (в днях)
    LOGS_RETENTION_DAYS: int = Field(default=30, env="LOGS_RETENTION_DAYS")
    ANALYTICS_RETENTION_DAYS: int = Field(default=365, env="ANALYTICS_RETENTION_DAYS")
    TEMP_FILES_RETENTION_DAYS: int = Field(default=7, env="TEMP_FILES_RETENTION_DAYS")
    
    # Настройки мониторинга
    DB_MONITORING_ENABLED: bool = Field(default=True, env="DB_MONITORING_ENABLED")
    SLOW_QUERY_THRESHOLD: float = Field(default=1.0, env="SLOW_QUERY_THRESHOLD")  # секунды
    
    # =============================================================================
    # НАСТРОЙКИ ТЕСТИРОВАНИЯ
    # =============================================================================
    
    # Тестовая база данных
    TEST_DATABASE_URL: str = Field(
        default="sqlite:///./test.db",
        env="TEST_DATABASE_URL"
    )
    
    # Тестовый Redis
    TEST_REDIS_HOST: str = Field(default="localhost", env="TEST_REDIS_HOST")
    TEST_REDIS_PORT: int = Field(default=6379, env="TEST_REDIS_PORT")
    TEST_REDIS_DB: int = Field(default=1, env="TEST_REDIS_DB")
    
    # Настройки тестов
    TEST_TIMEOUT: int = Field(default=30, env="TEST_TIMEOUT")
    TEST_PARALLEL: bool = Field(default=False, env="TEST_PARALLEL")
    
    # =============================================================================
    # НАСТРОЙКИ МОНИТОРИНГА
    # =============================================================================
    
    # Метрики
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_INTERVAL: int = Field(default=300, env="METRICS_INTERVAL")  # 5 минут
    
    # Здоровье приложения
    HEALTH_CHECK_ENABLED: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    HEALTH_CHECK_INTERVAL: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")  # 1 минута
    
    # =============================================================================
    # ВАЛИДАТОРЫ
    # =============================================================================
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v:
            return "dev-secret-key-change-in-production"
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        valid_prefixes = ["postgresql+asyncpg://", "sqlite+aiosqlite://"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError("DATABASE_URL должен начинаться с postgresql+asyncpg:// или sqlite+aiosqlite://")
        return v
    
    @validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        if v and len(v) < 32:
            raise ValueError("ENCRYPTION_KEY должен быть не менее 32 символов")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем глобальный экземпляр настроек
settings = Settings()

# Создаем папку для временных файлов если её нет
os.makedirs(settings.TEMP_DIR, exist_ok=True)

# Конфигурация для продакшена
class ProductionConfig(Settings):
    """Продакшн конфигурация"""
    
    # Railway автоматически предоставляет DATABASE_URL
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/realestate_bot",
        env="DATABASE_URL"
    )
    
    # Railway предоставляет PORT
    port: int = Field(default=8000, env="PORT")
    
    # Публичный URL для webhook'ов
    public_url: str = Field(default="", env="RAILWAY_PUBLIC_DOMAIN")
    
    # Остальные настройки наследуются от базового класса
    
    class Config:
        env_file = ".env" 