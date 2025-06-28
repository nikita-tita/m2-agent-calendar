"""
Система обработки ошибок и валидации
"""
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class RealEstateBotException(Exception):
    """Базовое исключение для бота недвижимости"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationException(RealEstateBotException):
    """Исключение для ошибок валидации"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})


class AuthenticationException(RealEstateBotException):
    """Исключение для ошибок аутентификации"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationException(RealEstateBotException):
    """Исключение для ошибок авторизации"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class NotFoundException(RealEstateBotException):
    """Исключение для ресурсов не найдено"""
    
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with id: {resource_id}"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "resource_id": resource_id})


class DatabaseException(RealEstateBotException):
    """Исключение для ошибок базы данных"""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation})


class ExternalServiceException(RealEstateBotException):
    """Исключение для ошибок внешних сервисов"""
    
    def __init__(self, service: str, message: str, status_code: int = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", {
            "service": service,
            "status_code": status_code
        })


class RateLimitException(RealEstateBotException):
    """Исключение для превышения лимитов"""
    
    def __init__(self, limit_type: str, retry_after: int = None):
        message = f"Rate limit exceeded for {limit_type}"
        super().__init__(message, "RATE_LIMIT_ERROR", {
            "limit_type": limit_type,
            "retry_after": retry_after
        })


class AIException(RealEstateBotException):
    """Исключение для ошибок AI сервисов"""
    
    def __init__(self, service: str, message: str):
        super().__init__(message, "AI_SERVICE_ERROR", {"service": service})


class CalendarException(RealEstateBotException):
    """Исключение для ошибок календаря"""
    
    def __init__(self, message: str, event_id: Any = None):
        super().__init__(message, "CALENDAR_ERROR", {"event_id": event_id})


class NotificationException(RealEstateBotException):
    """Исключение для ошибок уведомлений"""
    
    def __init__(self, channel: str, message: str):
        super().__init__(message, "NOTIFICATION_ERROR", {"channel": channel})


class AnalyticsException(RealEstateBotException):
    """Исключение для ошибок аналитики"""
    
    def __init__(self, message: str, report_type: str = None):
        super().__init__(message, "ANALYTICS_ERROR", {"report_type": report_type})


class EventNotFoundError(NotFoundException):
    """Исключение для ненайденных событий"""
    
    def __init__(self, event_id: Any = None):
        super().__init__("Event", event_id)


class UserNotFoundError(NotFoundException):
    """Исключение для ненайденных пользователей"""
    
    def __init__(self, user_id: Any = None):
        super().__init__("User", user_id)


class CacheException(RealEstateBotException):
    """Исключение для ошибок кэша"""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "CACHE_ERROR", {"operation": operation})


class ConfigException(RealEstateBotException):
    """Исключение для ошибок конфигурации"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})


def handle_exception(exc: Exception) -> HTTPException:
    """Преобразование внутренних исключений в HTTP исключения"""
    
    if isinstance(exc, ValidationException):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation Error",
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, AuthenticationException):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Authentication Error",
                "message": exc.message,
                "error_code": exc.error_code
            }
        )
    
    elif isinstance(exc, AuthorizationException):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Authorization Error",
                "message": exc.message,
                "error_code": exc.error_code
            }
        )
    
    elif isinstance(exc, NotFoundException):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Not Found",
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, RateLimitException):
        headers = {}
        if exc.details.get("retry_after"):
            headers["Retry-After"] = str(exc.details["retry_after"])
        
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate Limit Exceeded",
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            },
            headers=headers
        )
    
    elif isinstance(exc, (DatabaseException, ExternalServiceException, AIException)):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service Unavailable",
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    else:
        # Логирование неизвестной ошибки
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


class ErrorHandler:
    """Обработчик ошибок"""
    
    @staticmethod
    def log_error(exc: Exception, context: Dict[str, Any] = None):
        """Логирование ошибки"""
        logger.error(
            f"Error occurred: {type(exc).__name__}: {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": context or {}
            },
            exc_info=True
        )
    
    @staticmethod
    def format_error_response(exc: Exception) -> Dict[str, Any]:
        """Форматирование ответа с ошибкой"""
        if isinstance(exc, RealEstateBotException):
            return {
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        else:
            return {
                "success": False,
                "error": {
                    "code": "UNKNOWN_ERROR",
                    "message": str(exc),
                    "details": {}
                }
            }


class ValidationHelper:
    """Помощник для валидации"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация номера телефона"""
        import re
        # Российский формат: +7XXXXXXXXXX или 8XXXXXXXXXX
        pattern = r'^(\+7|8)[0-9]{10}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_price(price: Union[int, float]) -> bool:
        """Валидация цены"""
        return isinstance(price, (int, float)) and price > 0
    
    @staticmethod
    def validate_area(area: Union[int, float]) -> bool:
        """Валидация площади"""
        return isinstance(area, (int, float)) and area > 0
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Валидация координат"""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Очистка строки от потенциально опасных символов"""
        import re
        # Удаление HTML тегов
        text = re.sub(r'<[^>]+>', '', text)
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text).strip()
        # Ограничение длины
        if len(text) > max_length:
            text = text[:max_length]
        return text
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """Валидация размера файла (по умолчанию 10MB)"""
        return 0 < file_size <= max_size
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
        """Валидация типа файла"""
        if not allowed_extensions:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
        
        import os
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions


class ErrorCodes:
    """Коды ошибок"""
    
    # Общие ошибки
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"
    
    # Аутентификация и авторизация
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # База данных
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    
    # Внешние сервисы
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TELEGRAM_API_ERROR = "TELEGRAM_API_ERROR"
    OPENAI_API_ERROR = "OPENAI_API_ERROR"
    GOOGLE_API_ERROR = "GOOGLE_API_ERROR"
    
    # Ресурсы
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_BUSY = "RESOURCE_BUSY"
    
    # Лимиты
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # AI сервисы
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    SPEECH_RECOGNITION_ERROR = "SPEECH_RECOGNITION_ERROR"
    IMAGE_PROCESSING_ERROR = "IMAGE_PROCESSING_ERROR"
    
    # Календарь
    CALENDAR_ERROR = "CALENDAR_ERROR"
    EVENT_CONFLICT = "EVENT_CONFLICT"
    INVALID_DATE = "INVALID_DATE"
    
    # Уведомления
    NOTIFICATION_ERROR = "NOTIFICATION_ERROR"
    EMAIL_ERROR = "EMAIL_ERROR"
    SMS_ERROR = "SMS_ERROR"
    
    # Аналитика
    ANALYTICS_ERROR = "ANALYTICS_ERROR"
    REPORT_GENERATION_ERROR = "REPORT_GENERATION_ERROR"
    
    # Кэш
    CACHE_ERROR = "CACHE_ERROR"
    CACHE_MISS = "CACHE_MISS"
    
    # Файлы
    FILE_ERROR = "FILE_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    UPLOAD_ERROR = "UPLOAD_ERROR"


class ErrorMessages:
    """Сообщения об ошибках"""
    
    # Общие
    UNKNOWN_ERROR = "Произошла неизвестная ошибка"
    VALIDATION_ERROR = "Ошибка валидации данных"
    CONFIG_ERROR = "Ошибка конфигурации"
    
    # Аутентификация
    AUTHENTICATION_ERROR = "Ошибка аутентификации"
    AUTHORIZATION_ERROR = "Доступ запрещен"
    TOKEN_EXPIRED = "Токен истек"
    INVALID_TOKEN = "Недействительный токен"
    
    # База данных
    DATABASE_ERROR = "Ошибка базы данных"
    CONNECTION_ERROR = "Ошибка подключения к базе данных"
    QUERY_ERROR = "Ошибка выполнения запроса"
    
    # Внешние сервисы
    EXTERNAL_SERVICE_ERROR = "Ошибка внешнего сервиса"
    TELEGRAM_API_ERROR = "Ошибка Telegram API"
    OPENAI_API_ERROR = "Ошибка OpenAI API"
    GOOGLE_API_ERROR = "Ошибка Google API"
    
    # Ресурсы
    NOT_FOUND = "Ресурс не найден"
    ALREADY_EXISTS = "Ресурс уже существует"
    RESOURCE_BUSY = "Ресурс занят"
    
    # Лимиты
    RATE_LIMIT_ERROR = "Превышен лимит запросов"
    QUOTA_EXCEEDED = "Превышена квота"
    
    # AI сервисы
    AI_SERVICE_ERROR = "Ошибка AI сервиса"
    SPEECH_RECOGNITION_ERROR = "Ошибка распознавания речи"
    IMAGE_PROCESSING_ERROR = "Ошибка обработки изображения"
    
    # Календарь
    CALENDAR_ERROR = "Ошибка календаря"
    EVENT_CONFLICT = "Конфликт событий"
    INVALID_DATE = "Неверная дата"
    
    # Уведомления
    NOTIFICATION_ERROR = "Ошибка уведомления"
    EMAIL_ERROR = "Ошибка отправки email"
    SMS_ERROR = "Ошибка отправки SMS"
    
    # Аналитика
    ANALYTICS_ERROR = "Ошибка аналитики"
    REPORT_GENERATION_ERROR = "Ошибка генерации отчета"
    
    # Кэш
    CACHE_ERROR = "Ошибка кэша"
    CACHE_MISS = "Данные не найдены в кэше"
    
    # Файлы
    FILE_ERROR = "Ошибка файла"
    FILE_TOO_LARGE = "Файл слишком большой"
    INVALID_FILE_TYPE = "Неверный тип файла"
    UPLOAD_ERROR = "Ошибка загрузки файла" 