"""
Минимальная конфигурация без AI-сервисов
Для быстрого развёртывания в облаке
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class MinimalSettings(BaseSettings):
    """Минимальные настройки без AI"""
    
    # Основные настройки
    app_name: str = "M² Agent Calendar"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Telegram
    telegram_bot_token: str = Field(env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="webhook_secret", env="TELEGRAM_WEBHOOK_SECRET")
    
    # База данных
    database_url: str = Field(env="DATABASE_URL")
    
    # Отключение AI-сервисов
    enable_ai: bool = False
    enable_openai: bool = False
    enable_whisper: bool = False
    enable_vision: bool = False
    
    # Веб-сервер
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Публичный URL для webhook
    public_url: str = Field(default="", env="PUBLIC_URL")
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Экспорт настроек
settings = MinimalSettings() 