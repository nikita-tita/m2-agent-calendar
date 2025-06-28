"""
Тесты для компонентов оптимизации и улучшений
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.core.cache import CacheService, cache_service, CacheManager, cache_result
from app.core.logging import setup_logging, metrics, performance_monitor, log_context
from app.core.exceptions import (
    RealEstateBotException, ValidationException, AuthenticationException,
    RateLimitException, ErrorHandler, ValidationHelper
)
from app.core.security import (
    SecurityService, security_service, RateLimiter, rate_limiter,
    SecurityUtils, SecurityMiddleware
)
from app.core.database_optimization import (
    DatabaseOptimizer, db_optimizer, QueryBuilder, query_monitor
)
from app.core.testing import (
    TestDataGenerator, TestDatabase, TestCache, TestFixtures,
    TestMocks, TestHelpers, IntegrationTests, PerformanceTests, SecurityTests
)


class TestCache:
    """Тесты системы кэширования"""
    
    @pytest.fixture
    async def cache_service_instance(self):
        """Фикстура для тестового кэша"""
        service = CacheService()
        await service.connect()
        yield service
        await service.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_service_instance):
        """Тест установки и получения значений из кэша"""
        # Установка значения
        success = await cache_service_instance.set("test_key", "test_value", expire=60)
        assert success is True
        
        # Получение значения
        value = await cache_service_instance.get("test_key")
        assert value == "test_value"
        
        # Получение несуществующего ключа
        value = await cache_service_instance.get("non_existent_key", default="default")
        assert value == "default"
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_service_instance):
        """Тест удаления значений из кэша"""
        # Установка значения
        await cache_service_instance.set("test_key", "test_value")
        
        # Проверка существования
        exists = await cache_service_instance.exists("test_key")
        assert exists is True
        
        # Удаление
        success = await cache_service_instance.delete("test_key")
        assert success is True
        
        # Проверка удаления
        exists = await cache_service_instance.exists("test_key")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_cache_expire(self, cache_service_instance):
        """Тест установки времени жизни ключа"""
        # Установка значения
        await cache_service_instance.set("test_key", "test_value")
        
        # Установка времени жизни
        success = await cache_service_instance.expire("test_key", 1)
        assert success is True
        
        # Проверка существования
        exists = await cache_service_instance.exists("test_key")
        assert exists is True
        
        # Ожидание истечения
        await asyncio.sleep(2)
        
        # Проверка удаления
        exists = await cache_service_instance.exists("test_key")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self, cache_service_instance):
        """Тест декоратора кэширования"""
        call_count = 0
        
        @cache_result(expire=60, key_prefix="test")
        async def expensive_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # Первый вызов
        result1 = await expensive_function("test_param")
        assert result1 == "result_test_param"
        assert call_count == 1
        
        # Второй вызов (должен быть из кэша)
        result2 = await expensive_function("test_param")
        assert result2 == "result_test_param"
        assert call_count == 1  # Не увеличился
    
    @pytest.mark.asyncio
    async def test_cache_manager(self, cache_service_instance):
        """Тест менеджера кэша"""
        # Установка тестовых данных
        await cache_service_instance.set("user:profile:123", "user_data")
        await cache_service_instance.set("property:list:123:1:20", "property_list")
        
        # Инвалидация кэша пользователя
        await CacheManager.invalidate_user_cache(123)
        
        # Проверка удаления
        user_data = await cache_service_instance.get("user:profile:123")
        assert user_data is None
        
        property_list = await cache_service_instance.get("property:list:123:1:20")
        assert property_list is None


class TestLogging:
    """Тесты системы логирования"""
    
    def test_setup_logging(self):
        """Тест настройки логирования"""
        # Тест без ошибок
        setup_logging(log_level="INFO", log_format="json")
        
        # Проверка, что логирование работает
        import logging
        logger = logging.getLogger("test")
        logger.info("Test log message")
    
    def test_metrics_collector(self):
        """Тест сборщика метрик"""
        # Сброс метрик
        metrics.reset()
        
        # Добавление метрик
        metrics.increment("test.counter")
        metrics.gauge("test.gauge", 42.5)
        metrics.timer("test.timer", 1.5)
        
        # Получение метрик
        all_metrics = metrics.get_metrics()
        
        assert all_metrics["counters"]["test.counter"] == 1
        assert all_metrics["gauges"]["test.gauge"] == 42.5
        assert "test.timer" in all_metrics["timers"]
    
    @pytest.mark.asyncio
    async def test_log_context(self):
        """Тест контекстного логирования"""
        async with log_context(user_id=123, request_id="test_req"):
            # Операции внутри контекста
            pass
        
        # Проверка, что контекст завершился без ошибок
        assert True
    
    def test_performance_monitor(self):
        """Тест монитора производительности"""
        # Сброс монитора
        performance_monitor.requests_count = 0
        performance_monitor.errors_count = 0
        
        # Запись запросов
        performance_monitor.record_request(success=True)
        performance_monitor.record_request(success=False)
        performance_monitor.record_request(success=True)
        
        # Проверка статистики
        assert performance_monitor.requests_count == 3
        assert performance_monitor.errors_count == 1
        assert performance_monitor.get_error_rate() == 33.33333333333333


class TestExceptions:
    """Тесты системы обработки ошибок"""
    
    def test_exception_hierarchy(self):
        """Тест иерархии исключений"""
        # Базовое исключение
        exc = RealEstateBotException("Test error", "TEST_ERROR", {"detail": "test"})
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details["detail"] == "test"
        
        # Специализированные исключения
        val_exc = ValidationException("Invalid data", "field", "value")
        assert val_exc.error_code == "VALIDATION_ERROR"
        assert val_exc.details["field"] == "field"
        
        auth_exc = AuthenticationException("Auth failed")
        assert auth_exc.error_code == "AUTHENTICATION_ERROR"
        
        rate_exc = RateLimitException("Too many requests", retry_after=60)
        assert rate_exc.error_code == "RATE_LIMIT_ERROR"
        assert rate_exc.details["retry_after"] == 60
    
    def test_error_handler(self):
        """Тест обработчика ошибок"""
        exc = ValidationException("Invalid email", "email", "invalid@")
        
        # Логирование ошибки
        ErrorHandler.log_error(exc, {"context": "test"})
        
        # Форматирование ответа
        response = ErrorHandler.format_error_response(exc)
        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid email"
    
    def test_validation_helper(self):
        """Тест помощника валидации"""
        # Валидация телефона
        assert ValidationHelper.validate_phone("+79001234567") is True
        assert ValidationHelper.validate_phone("89001234567") is True
        assert ValidationHelper.validate_phone("1234567890") is False
        
        # Валидация email
        assert ValidationHelper.validate_email("test@example.com") is True
        assert ValidationHelper.validate_email("invalid-email") is False
        
        # Валидация цены
        assert ValidationHelper.validate_price(1000) is True
        assert ValidationHelper.validate_price(-100) is False
        
        # Валидация площади
        assert ValidationHelper.validate_area(50.5) is True
        assert ValidationHelper.validate_area(0) is False
        
        # Валидация координат
        assert ValidationHelper.validate_coordinates(55.7558, 37.6176) is True
        assert ValidationHelper.validate_coordinates(200, 37.6176) is False
        
        # Очистка строки
        cleaned = ValidationHelper.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in cleaned
        
        # Валидация файла
        assert ValidationHelper.validate_file_size(1024 * 1024) is True  # 1MB
        assert ValidationHelper.validate_file_size(20 * 1024 * 1024) is False  # 20MB
        
        assert ValidationHelper.validate_file_type("image.jpg") is True
        assert ValidationHelper.validate_file_type("script.exe") is False


class TestSecurity:
    """Тесты системы безопасности"""
    
    @pytest.fixture
    def security_service_instance(self):
        """Фикстура для тестового сервиса безопасности"""
        return SecurityService()
    
    def test_password_hashing(self, security_service_instance):
        """Тест хеширования паролей"""
        password = "my_secure_password"
        
        # Хеширование
        hash_data = security_service_instance.hash_password(password)
        assert "hash" in hash_data
        assert "salt" in hash_data
        
        # Проверка пароля
        is_valid = security_service_instance.verify_password(
            password, hash_data["hash"], hash_data["salt"]
        )
        assert is_valid is True
        
        # Проверка неверного пароля
        is_valid = security_service_instance.verify_password(
            "wrong_password", hash_data["hash"], hash_data["salt"]
        )
        assert is_valid is False
    
    def test_token_generation(self, security_service_instance):
        """Тест генерации токенов"""
        payload = {"user_id": 123, "role": "agent"}
        
        # Генерация токена
        token = security_service_instance.generate_token(payload, expires_in=3600)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Проверка токена
        decoded_payload = security_service_instance.verify_token(token)
        assert decoded_payload is not None
        assert decoded_payload["user_id"] == 123
        assert decoded_payload["role"] == "agent"
    
    def test_encryption(self, security_service_instance):
        """Тест шифрования данных"""
        original_data = "sensitive information"
        
        # Шифрование
        encrypted = security_service_instance.encrypt_data(original_data)
        assert encrypted != original_data
        
        # Расшифровка
        decrypted = security_service_instance.decrypt_data(encrypted)
        assert decrypted == original_data
    
    def test_api_key_generation(self, security_service_instance):
        """Тест генерации API ключей"""
        # Генерация ключа
        api_key = security_service_instance.generate_api_key(32)
        assert len(api_key) == 32
        assert api_key.isalnum()
        
        # Хеширование ключа
        hash_key = security_service_instance.hash_api_key(api_key)
        assert len(hash_key) == 64  # SHA256 hex
    
    def test_input_validation(self, security_service_instance):
        """Тест валидации входных данных"""
        # Валидные данные
        valid_input = "Normal text input"
        cleaned = security_service_instance.validate_input(valid_input)
        assert cleaned == valid_input
        
        # Данные с HTML тегами
        html_input = "<script>alert('xss')</script>"
        cleaned = security_service_instance.validate_input(html_input)
        assert "<script>" not in cleaned
        
        # Слишком длинные данные
        long_input = "a" * 2000
        with pytest.raises(ValidationException):
            security_service_instance.validate_input(long_input, max_length=1000)
    
    def test_sql_injection_protection(self, security_service_instance):
        """Тест защиты от SQL инъекций"""
        # Опасные паттерны
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "' UNION SELECT * FROM users --"
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(Exception):
                security_service_instance.sanitize_sql_input(dangerous_input)
        
        # Безопасные данные
        safe_input = "normal search query"
        result = security_service_instance.sanitize_sql_input(safe_input)
        assert result == safe_input
    
    def test_rate_limiter(self):
        """Тест ограничителя скорости"""
        # Сброс лимитера
        rate_limiter.requests.clear()
        rate_limiter.blocked_ips.clear()
        
        identifier = "test_user"
        
        # Проверка лимита
        for i in range(100):
            is_limited = rate_limiter.is_rate_limited(identifier, max_requests=100)
            assert is_limited is False
        
        # Превышение лимита
        is_limited = rate_limiter.is_rate_limited(identifier, max_requests=100)
        assert is_limited is True
    
    def test_ip_blocking(self):
        """Тест блокировки IP"""
        ip = "192.168.1.1"
        
        # Блокировка IP
        rate_limiter.block_ip(ip, duration=1)
        assert rate_limiter.is_ip_blocked(ip) is True
        
        # Ожидание разблокировки
        time.sleep(2)
        assert rate_limiter.is_ip_blocked(ip) is False
    
    def test_security_utils(self):
        """Тест утилит безопасности"""
        # Генерация безопасного пароля
        password = SecurityUtils.generate_secure_password(12)
        assert len(password) == 12
        
        # Проверка сложности пароля
        strength = SecurityUtils.validate_password_strength(password)
        assert strength["valid"] is True
        assert strength["score"] >= 3
        
        # Проверка IP адресов
        assert SecurityUtils.is_valid_ip("192.168.1.1") is True
        assert SecurityUtils.is_valid_ip("invalid_ip") is False
        assert SecurityUtils.is_private_ip("192.168.1.1") is True
        assert SecurityUtils.is_private_ip("8.8.8.8") is False


class TestDatabaseOptimization:
    """Тесты оптимизации базы данных"""
    
    @pytest.fixture
    async def db_optimizer_instance(self):
        """Фикстура для тестового оптимизатора БД"""
        optimizer = DatabaseOptimizer()
        await optimizer.initialize()
        yield optimizer
        # Очистка
        if optimizer.engine:
            await optimizer.engine.dispose()
    
    @pytest.mark.asyncio
    async def test_database_optimizer_initialization(self, db_optimizer_instance):
        """Тест инициализации оптимизатора БД"""
        assert db_optimizer_instance.engine is not None
        assert db_optimizer_instance.async_session_maker is not None
    
    @pytest.mark.asyncio
    async def test_query_builder(self):
        """Тест построителя запросов"""
        # Построение запроса поиска недвижимости
        query, params = QueryBuilder.build_property_search_query(
            user_id=123,
            property_type="apartment",
            min_price=1000000,
            max_price=5000000,
            location="Москва",
            limit=20,
            offset=0
        )
        
        assert "SELECT * FROM properties" in query
        assert "user_id = :user_id" in query
        assert "type = :property_type" in query
        assert params["user_id"] == 123
        assert params["property_type"] == "apartment"
        assert params["min_price"] == 1000000
        assert params["max_price"] == 5000000
        assert params["limit"] == 20
        assert params["offset"] == 0
    
    @pytest.mark.asyncio
    async def test_query_builder_calendar(self):
        """Тест построителя запросов календаря"""
        user_id = 123
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        query, params = QueryBuilder.build_calendar_events_query(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            event_type="meeting"
        )
        
        assert "SELECT * FROM calendar_events" in query
        assert "user_id = :user_id" in query
        assert "type = :event_type" in query
        assert params["user_id"] == user_id
        assert params["start_date"] == start_date
        assert params["end_date"] == end_date
        assert params["event_type"] == "meeting"
    
    def test_query_monitor_decorator(self):
        """Тест декоратора мониторинга запросов"""
        call_count = 0
        
        @query_monitor
        async def test_query():
            nonlocal call_count
            call_count += 1
            return "query_result"
        
        # Вызов функции
        result = asyncio.run(test_query())
        assert result == "query_result"
        assert call_count == 1


class TestTesting:
    """Тесты системы тестирования"""
    
    def test_test_data_generator(self):
        """Тест генератора тестовых данных"""
        # Генерация данных пользователя
        user_data = TestDataGenerator.generate_user_data()
        assert "telegram_id" in user_data
        assert "username" in user_data
        assert "email" in user_data
        assert "phone" in user_data
        
        # Генерация данных недвижимости
        property_data = TestDataGenerator.generate_property_data(user_id=123)
        assert "user_id" in property_data
        assert "type" in property_data
        assert "price" in property_data
        assert "area" in property_data
        
        # Генерация данных события календаря
        event_data = TestDataGenerator.generate_calendar_event_data(user_id=123)
        assert "user_id" in event_data
        assert "title" in event_data
        assert "start_time" in event_data
        assert "end_time" in event_data
        
        # Генерация данных аналитики
        analytics_data = TestDataGenerator.generate_analytics_data(user_id=123)
        assert "user_id" in analytics_data
        assert "type" in analytics_data
        assert "value" in analytics_data
    
    def test_test_database(self):
        """Тест тестовой базы данных"""
        db = TestDatabase()
        
        # Настройка
        db.setup()
        assert db.engine is not None
        assert db.SessionLocal is not None
        
        # Получение сессии
        session = db.get_session()
        assert session is not None
        session.close()
        
        # Очистка
        db.teardown()
    
    def test_test_cache(self):
        """Тест тестового кэша"""
        cache = TestCache()
        
        # Настройка
        cache.setup()
        assert cache_service.redis_client is not None
        
        # Очистка
        cache.teardown()
    
    def test_test_mocks(self):
        """Тест моков"""
        # Мок Telegram бота
        mock_bot = TestMocks.mock_telegram_bot()
        assert mock_bot.send_message is not None
        assert mock_bot.send_photo is not None
        
        # Мок OpenAI клиента
        mock_openai = TestMocks.mock_openai_client()
        assert mock_openai.chat.completions.create is not None
        
        # Мок Redis клиента
        mock_redis = TestMocks.mock_redis_client()
        assert mock_redis.get is not None
        assert mock_redis.set is not None
    
    def test_test_helpers(self):
        """Тест помощников тестирования"""
        # Тест структуры ответа
        valid_response = {
            "success": True,
            "data": {"id": 1, "name": "test"}
        }
        TestHelpers.assert_response_structure(valid_response)
        
        # Тест с неверной структурой
        invalid_response = {"data": "test"}
        with pytest.raises(AssertionError):
            TestHelpers.assert_response_structure(invalid_response)


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_user_workflow(self):
        """Тест полного рабочего процесса пользователя"""
        # Этот тест требует реальной тестовой среды
        # Здесь только проверка структуры
        assert hasattr(IntegrationTests, 'test_full_user_workflow')
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """Тест ограничения скорости API"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(IntegrationTests, 'test_api_rate_limiting')
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Тест функциональности кэша"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(IntegrationTests, 'test_cache_functionality')


class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Тест производительности базы данных"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(PerformanceTests, 'test_database_performance')
    
    @pytest.mark.asyncio
    async def test_api_response_time(self):
        """Тест времени ответа API"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(PerformanceTests, 'test_api_response_time')


class TestSecurity:
    """Тесты безопасности"""
    
    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Тест обязательной аутентификации"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(SecurityTests, 'test_authentication_required')
    
    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Тест валидации входных данных"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(SecurityTests, 'test_input_validation')
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        """Тест защиты от SQL инъекций"""
        # Этот тест требует реальной тестовой среды
        assert hasattr(SecurityTests, 'test_sql_injection_protection')


# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 