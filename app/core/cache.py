"""
Система кэширования для оптимизации производительности
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import hashlib
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Сервис кэширования с Redis"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._prefix = "realestate_bot:"
        
    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache disconnected")
    
    def _get_key(self, key: str) -> str:
        """Получение полного ключа с префиксом"""
        return f"{self._prefix}{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из кэша"""
        if not self.redis_client:
            return default
        
        try:
            full_key = self._get_key(key)
            data = await self.redis_client.get(full_key)
            if data:
                return pickle.loads(data)
            return default
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Установка значения в кэш"""
        if not self.redis_client:
            return False
        
        try:
            full_key = self._get_key(key)
            data = pickle.dumps(value)
            await self.redis_client.set(full_key, data, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if not self.redis_client:
            return False
        
        try:
            full_key = self._get_key(key)
            await self.redis_client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self.redis_client:
            return False
        
        try:
            full_key = self._get_key(key)
            return await self.redis_client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Установка времени жизни ключа"""
        if not self.redis_client:
            return False
        
        try:
            full_key = self._get_key(key)
            return await self.redis_client.expire(full_key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка ключей по паттерну"""
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = self._get_key(pattern)
            keys = await self.redis_client.keys(full_pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Получение множества значений"""
        if not self.redis_client:
            return {}
        
        try:
            full_keys = [self._get_key(key) for key in keys]
            values = await self.redis_client.mget(full_keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = pickle.loads(value)
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(self, data: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Установка множества значений"""
        if not self.redis_client:
            return False
        
        try:
            pipeline = self.redis_client.pipeline()
            for key, value in data.items():
                full_key = self._get_key(key)
                data_bytes = pickle.dumps(value)
                pipeline.set(full_key, data_bytes, ex=expire)
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False


# Глобальный экземпляр кэша
cache_service = CacheService()


def cache_result(expire: int = 300, key_prefix: str = ""):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        expire: Время жизни кэша в секундах
        key_prefix: Префикс для ключа кэша
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создание ключа кэша
            cache_key_parts = [key_prefix, func.__name__]
            
            # Добавление аргументов в ключ
            if args:
                cache_key_parts.append(str(hash(str(args))))
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                cache_key_parts.append(str(hash(str(sorted_kwargs))))
            
            cache_key = ":".join(cache_key_parts)
            
            # Попытка получить из кэша
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Сохранение в кэш
            await cache_service.set(cache_key, result, expire)
            logger.debug(f"Cache set for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


class CacheKeys:
    """Константы для ключей кэша"""
    
    # Пользователи
    USER_PROFILE = "user:profile:{user_id}"
    USER_SETTINGS = "user:settings:{user_id}"
    
    # Недвижимость
    PROPERTY_LIST = "property:list:{user_id}:{page}:{limit}"
    PROPERTY_DETAIL = "property:detail:{property_id}"
    PROPERTY_SEARCH = "property:search:{query_hash}"
    
    # Календарь
    CALENDAR_EVENTS = "calendar:events:{user_id}:{date}"
    CALENDAR_STATS = "calendar:stats:{user_id}:{period}"
    
    # Аналитика
    ANALYTICS_REPORT = "analytics:report:{user_id}:{report_type}:{period}"
    ANALYTICS_DASHBOARD = "analytics:dashboard:{user_id}"
    
    # AI
    AI_RESPONSE = "ai:response:{query_hash}"
    AI_PROPERTY_PARSE = "ai:property:parse:{image_hash}"
    
    # API
    API_RATE_LIMIT = "api:rate_limit:{user_id}"
    API_TOKEN = "api:token:{token_hash}"


class CacheManager:
    """Менеджер кэша для бизнес-логики"""
    
    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Инвалидация кэша пользователя"""
        patterns = [
            f"user:profile:{user_id}",
            f"user:settings:{user_id}",
            f"property:list:{user_id}:*",
            f"calendar:events:{user_id}:*",
            f"calendar:stats:{user_id}:*",
            f"analytics:report:{user_id}:*",
            f"analytics:dashboard:{user_id}"
        ]
        
        for pattern in patterns:
            await cache_service.clear_pattern(pattern)
    
    @staticmethod
    async def invalidate_property_cache(property_id: int):
        """Инвалидация кэша недвижимости"""
        patterns = [
            f"property:detail:{property_id}",
            "property:list:*",
            "property:search:*"
        ]
        
        for pattern in patterns:
            await cache_service.clear_pattern(pattern)
    
    @staticmethod
    async def invalidate_calendar_cache(user_id: int, date: Optional[str] = None):
        """Инвалидация кэша календаря"""
        if date:
            patterns = [
                f"calendar:events:{user_id}:{date}",
                f"calendar:stats:{user_id}:*"
            ]
        else:
            patterns = [
                f"calendar:events:{user_id}:*",
                f"calendar:stats:{user_id}:*"
            ]
        
        for pattern in patterns:
            await cache_service.clear_pattern(pattern)
    
    @staticmethod
    async def invalidate_analytics_cache(user_id: int):
        """Инвалидация кэша аналитики"""
        patterns = [
            f"analytics:report:{user_id}:*",
            f"analytics:dashboard:{user_id}"
        ]
        
        for pattern in patterns:
            await cache_service.clear_pattern(pattern) 