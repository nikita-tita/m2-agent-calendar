"""
Система тестирования и CI/CD
"""
import pytest
import asyncio
from typing import Dict, List, Any, Optional, Generator
from unittest.mock import Mock, AsyncMock, patch
import json
import tempfile
import shutil
from pathlib import Path
import logging
from datetime import datetime, timedelta
import random
import string

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.config import settings
from app.database import get_db, Base
from app.main import app
from app.models.user import User
from app.models.property import Property
from app.models.calendar import CalendarEvent
from app.core.security import security_service
from app.core.cache import cache_service

logger = logging.getLogger(__name__)


class TestConfig:
    """Конфигурация для тестов"""
    
    # База данных для тестов
    TEST_DATABASE_URL = "sqlite:///./test.db"
    
    # Настройки кэша
    TEST_REDIS_HOST = "localhost"
    TEST_REDIS_PORT = 6379
    TEST_REDIS_DB = 1
    
    # Настройки безопасности
    TEST_SECRET_KEY = "test-secret-key-for-testing-only"
    
    # Лимиты для тестов
    TEST_RATE_LIMIT = 1000
    TEST_MAX_FILE_SIZE = 1024 * 1024  # 1MB


class TestDataGenerator:
    """Генератор тестовых данных"""
    
    @staticmethod
    def generate_user_data(**kwargs) -> Dict[str, Any]:
        """Генерация данных пользователя"""
        default_data = {
            "telegram_id": random.randint(100000000, 999999999),
            "username": f"test_user_{random.randint(1000, 9999)}",
            "first_name": f"Test{random.randint(1, 100)}",
            "last_name": f"User{random.randint(1, 100)}",
            "email": f"test{random.randint(1, 1000)}@example.com",
            "phone": f"+7{random.randint(9000000000, 9999999999)}",
            "status": "active",
            "role": "agent",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def generate_property_data(user_id: int, **kwargs) -> Dict[str, Any]:
        """Генерация данных недвижимости"""
        property_types = ["apartment", "house", "commercial", "land"]
        statuses = ["active", "sold", "rented", "inactive"]
        
        default_data = {
            "user_id": user_id,
            "type": random.choice(property_types),
            "status": random.choice(statuses),
            "title": f"Test Property {random.randint(1, 1000)}",
            "description": f"Test description for property {random.randint(1, 1000)}",
            "price": random.randint(1000000, 50000000),
            "area": random.randint(30, 200),
            "rooms": random.randint(1, 5),
            "floor": random.randint(1, 25),
            "total_floors": random.randint(5, 30),
            "address": f"Test Address {random.randint(1, 1000)}",
            "latitude": random.uniform(55.0, 56.0),
            "longitude": random.uniform(37.0, 38.0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def generate_calendar_event_data(user_id: int, **kwargs) -> Dict[str, Any]:
        """Генерация данных события календаря"""
        event_types = ["meeting", "showing", "call", "reminder"]
        statuses = ["scheduled", "completed", "cancelled"]
        
        start_time = datetime.utcnow() + timedelta(days=random.randint(1, 30))
        end_time = start_time + timedelta(hours=random.randint(1, 3))
        
        default_data = {
            "user_id": user_id,
            "title": f"Test Event {random.randint(1, 1000)}",
            "description": f"Test description for event {random.randint(1, 1000)}",
            "type": random.choice(event_types),
            "status": random.choice(statuses),
            "start_time": start_time,
            "end_time": end_time,
            "location": f"Test Location {random.randint(1, 100)}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def generate_analytics_data(user_id: int, **kwargs) -> Dict[str, Any]:
        """Генерация данных аналитики"""
        analytics_types = ["views", "contacts", "sales", "revenue"]
        
        default_data = {
            "user_id": user_id,
            "type": random.choice(analytics_types),
            "value": random.randint(1, 1000),
            "date": datetime.utcnow().date(),
            "created_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


class TestDatabase:
    """Управление тестовой базой данных"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.test_db_path = None
    
    def setup(self):
        """Настройка тестовой базы данных"""
        # Создание временного файла базы данных
        self.test_db_path = tempfile.mktemp(suffix=".db")
        
        # Создание движка для тестов
        self.engine = create_engine(
            f"sqlite:///{self.test_db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Создание таблиц
        Base.metadata.create_all(bind=self.engine)
        
        logger.info(f"Test database created: {self.test_db_path}")
    
    def teardown(self):
        """Очистка тестовой базы данных"""
        if self.engine:
            self.engine.dispose()
        
        if self.test_db_path and Path(self.test_db_path).exists():
            Path(self.test_db_path).unlink()
        
        logger.info("Test database cleaned up")
    
    def get_session(self):
        """Получение сессии тестовой базы данных"""
        return self.SessionLocal()
    
    def clear_data(self):
        """Очистка данных из тестовой базы"""
        session = self.get_session()
        try:
            # Удаление всех данных из таблиц
            session.query(CalendarEvent).delete()
            session.query(Property).delete()
            session.query(User).delete()
            session.commit()
        finally:
            session.close()


class TestCache:
    """Управление тестовым кэшем"""
    
    def __init__(self):
        self.original_cache = None
    
    def setup(self):
        """Настройка тестового кэша"""
        # Сохранение оригинального кэша
        self.original_cache = cache_service.redis_client
        
        # Создание мока для кэша
        cache_service.redis_client = Mock()
        cache_service.redis_client.get = AsyncMock(return_value=None)
        cache_service.redis_client.set = AsyncMock(return_value=True)
        cache_service.redis_client.delete = AsyncMock(return_value=True)
        cache_service.redis_client.exists = AsyncMock(return_value=0)
    
    def teardown(self):
        """Восстановление оригинального кэша"""
        if self.original_cache:
            cache_service.redis_client = self.original_cache


class TestFixtures:
    """Фикстуры для тестов"""
    
    @staticmethod
    @pytest.fixture
    def test_db():
        """Фикстура тестовой базы данных"""
        db = TestDatabase()
        db.setup()
        yield db
        db.teardown()
    
    @staticmethod
    @pytest.fixture
    def test_cache():
        """Фикстура тестового кэша"""
        cache = TestCache()
        cache.setup()
        yield cache
        cache.teardown()
    
    @staticmethod
    @pytest.fixture
    def test_client():
        """Фикстура тестового клиента"""
        return TestClient(app)
    
    @staticmethod
    @pytest.fixture
    async def async_client():
        """Фикстура асинхронного тестового клиента"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @staticmethod
    @pytest.fixture
    def sample_user(test_db):
        """Фикстура тестового пользователя"""
        session = test_db.get_session()
        try:
            user_data = TestDataGenerator.generate_user_data()
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()
    
    @staticmethod
    @pytest.fixture
    def sample_property(test_db, sample_user):
        """Фикстура тестовой недвижимости"""
        session = test_db.get_session()
        try:
            property_data = TestDataGenerator.generate_property_data(sample_user.id)
            property_obj = Property(**property_data)
            session.add(property_obj)
            session.commit()
            session.refresh(property_obj)
            return property_obj
        finally:
            session.close()
    
    @staticmethod
    @pytest.fixture
    def sample_calendar_event(test_db, sample_user):
        """Фикстура тестового события календаря"""
        session = test_db.get_session()
        try:
            event_data = TestDataGenerator.generate_calendar_event_data(sample_user.id)
            event = CalendarEvent(**event_data)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        finally:
            session.close()
    
    @staticmethod
    @pytest.fixture
    def auth_headers(sample_user):
        """Фикстура заголовков аутентификации"""
        token = security_service.generate_token({"user_id": sample_user.id})
        return {"Authorization": f"Bearer {token}"}


class TestMocks:
    """Моки для тестов"""
    
    @staticmethod
    def mock_telegram_bot():
        """Мок Telegram бота"""
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()
        mock_bot.send_photo = AsyncMock()
        mock_bot.send_document = AsyncMock()
        mock_bot.edit_message_text = AsyncMock()
        mock_bot.delete_message = AsyncMock()
        return mock_bot
    
    @staticmethod
    def mock_openai_client():
        """Мок OpenAI клиента"""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(message=Mock(content="Test AI response"))]
        ))
        mock_client.audio.transcriptions.create = AsyncMock(return_value=Mock(
            text="Test transcribed text"
        ))
        return mock_client
    
    @staticmethod
    def mock_redis_client():
        """Мок Redis клиента"""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.expire = AsyncMock(return_value=True)
        return mock_redis
    
    @staticmethod
    def mock_email_service():
        """Мок сервиса email"""
        mock_service = Mock()
        mock_service.send_email = AsyncMock(return_value=True)
        mock_service.send_bulk_email = AsyncMock(return_value=True)
        return mock_service
    
    @staticmethod
    def mock_sms_service():
        """Мок сервиса SMS"""
        mock_service = Mock()
        mock_service.send_sms = AsyncMock(return_value=True)
        mock_service.send_bulk_sms = AsyncMock(return_value=True)
        return mock_service


class TestHelpers:
    """Помощники для тестов"""
    
    @staticmethod
    def assert_response_structure(response_data: Dict[str, Any]):
        """Проверка структуры ответа API"""
        assert "success" in response_data
        if response_data["success"]:
            assert "data" in response_data
        else:
            assert "error" in response_data
            assert "code" in response_data["error"]
            assert "message" in response_data["error"]
    
    @staticmethod
    def assert_user_data(user_data: Dict[str, Any], expected_user: User):
        """Проверка данных пользователя"""
        assert user_data["id"] == expected_user.id
        assert user_data["telegram_id"] == expected_user.telegram_id
        assert user_data["username"] == expected_user.username
        assert user_data["email"] == expected_user.email
    
    @staticmethod
    def assert_property_data(property_data: Dict[str, Any], expected_property: Property):
        """Проверка данных недвижимости"""
        assert property_data["id"] == expected_property.id
        assert property_data["user_id"] == expected_property.user_id
        assert property_data["type"] == expected_property.type
        assert property_data["title"] == expected_property.title
        assert property_data["price"] == expected_property.price
    
    @staticmethod
    def assert_calendar_event_data(event_data: Dict[str, Any], expected_event: CalendarEvent):
        """Проверка данных события календаря"""
        assert event_data["id"] == expected_event.id
        assert event_data["user_id"] == expected_event.user_id
        assert event_data["title"] == expected_event.title
        assert event_data["type"] == expected_event.type
        assert event_data["start_time"] == expected_event.start_time.isoformat()


class IntegrationTests:
    """Интеграционные тесты"""
    
    @staticmethod
    async def test_full_user_workflow(test_client, test_db, auth_headers):
        """Тест полного рабочего процесса пользователя"""
        # Создание пользователя
        user_data = TestDataGenerator.generate_user_data()
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Создание недвижимости
        property_data = TestDataGenerator.generate_property_data(user_data["telegram_id"])
        response = test_client.post("/api/properties/", json=property_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Создание события календаря
        event_data = TestDataGenerator.generate_calendar_event_data(user_data["telegram_id"])
        response = test_client.post("/api/calendar/events/", json=event_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Получение аналитики
        response = test_client.get("/api/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
    
    @staticmethod
    async def test_api_rate_limiting(test_client, test_db):
        """Тест ограничения скорости API"""
        # Множественные запросы для проверки лимита
        for i in range(105):  # Больше лимита
            response = test_client.get("/api/health")
            if i < 100:
                assert response.status_code == 200
            else:
                assert response.status_code == 429  # Too Many Requests
    
    @staticmethod
    async def test_cache_functionality(test_client, test_db, auth_headers):
        """Тест функциональности кэша"""
        # Первый запрос (должен кэшироваться)
        response1 = test_client.get("/api/properties/", headers=auth_headers)
        assert response1.status_code == 200
        
        # Второй запрос (должен быть из кэша)
        response2 = test_client.get("/api/properties/", headers=auth_headers)
        assert response2.status_code == 200
        
        # Проверка, что данные одинаковые
        assert response1.json() == response2.json()


class PerformanceTests:
    """Тесты производительности"""
    
    @staticmethod
    async def test_database_performance(test_db):
        """Тест производительности базы данных"""
        session = test_db.get_session()
        
        try:
            # Создание множества пользователей
            start_time = datetime.utcnow()
            
            users = []
            for i in range(1000):
                user_data = TestDataGenerator.generate_user_data()
                user = User(**user_data)
                users.append(user)
            
            session.add_all(users)
            session.commit()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Проверка, что создание 1000 пользователей занимает менее 5 секунд
            assert duration < 5.0
            
            # Тест поиска
            start_time = datetime.utcnow()
            found_users = session.query(User).filter(User.status == "active").all()
            end_time = datetime.utcnow()
            search_duration = (end_time - start_time).total_seconds()
            
            # Проверка, что поиск занимает менее 1 секунды
            assert search_duration < 1.0
            
        finally:
            session.close()
    
    @staticmethod
    async def test_api_response_time(test_client, test_db, auth_headers):
        """Тест времени ответа API"""
        import time
        
        # Тест времени ответа для различных эндпоинтов
        endpoints = [
            "/api/health",
            "/api/properties/",
            "/api/calendar/events/",
            "/api/analytics/dashboard"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = test_client.get(endpoint, headers=auth_headers)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Проверка, что ответ занимает менее 500ms
            assert duration < 0.5
            assert response.status_code in [200, 201, 404]


class SecurityTests:
    """Тесты безопасности"""
    
    @staticmethod
    async def test_authentication_required(test_client, test_db):
        """Тест обязательной аутентификации"""
        protected_endpoints = [
            "/api/properties/",
            "/api/calendar/events/",
            "/api/analytics/dashboard",
            "/api/users/profile"
        ]
        
        for endpoint in protected_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
    
    @staticmethod
    async def test_input_validation(test_client, test_db, auth_headers):
        """Тест валидации входных данных"""
        # Тест с неверными данными
        invalid_property_data = {
            "type": "invalid_type",
            "price": -1000,
            "area": 0
        }
        
        response = test_client.post("/api/properties/", json=invalid_property_data, headers=auth_headers)
        assert response.status_code == 422  # Unprocessable Entity
    
    @staticmethod
    async def test_sql_injection_protection(test_client, test_db, auth_headers):
        """Тест защиты от SQL инъекций"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = test_client.get(f"/api/properties/?search={malicious_input}", headers=auth_headers)
            # Должен вернуть ошибку или пустой результат, но не упасть
            assert response.status_code in [200, 400, 422]


# Конфигурация pytest
def pytest_configure(config):
    """Конфигурация pytest"""
    # Настройка логирования для тестов
    logging.basicConfig(level=logging.WARNING)
    
    # Отключение логирования для внешних библиотек
    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов"""
    # Добавление маркеров для различных типов тестов
    for item in items:
        if "test_full_user_workflow" in item.name:
            item.add_marker(pytest.mark.integration)
        elif "test_database_performance" in item.name:
            item.add_marker(pytest.mark.performance)
        elif "test_authentication_required" in item.name:
            item.add_marker(pytest.mark.security) 