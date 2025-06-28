"""
Конфигурация для тестов
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.main import app
from app.database import get_async_session
from app.models import Base


# Тестовая база данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Создаем тестовый движок базы данных
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Создаем тестовую сессию
TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Переопределение зависимости для получения сессии базы данных"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Настройка тестовой базы данных"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для получения сессии базы данных"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для HTTP клиента"""
    # Переопределяем зависимость
    app.dependency_overrides[get_async_session] = lambda: db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Очищаем переопределения
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Тестовые настройки"""
    return {
        "SECRET_KEY": "test-secret-key",
        "DEBUG": True,
        "ALLOWED_HOSTS": ["*"],
        "DATABASE_URL": TEST_DATABASE_URL,
        "OPENAI_API_KEY": "test-openai-key",
        "TELEGRAM_BOT_TOKEN": "test-telegram-token",
    }


# Фикстуры для тестовых данных
@pytest.fixture
def sample_property_data():
    """Тестовые данные для объекта недвижимости"""
    return {
        "title": "Тестовая квартира",
        "description": "Описание тестовой квартиры",
        "property_type": "apartment",
        "deal_type": "sale",
        "price": 5000000.0,
        "area": 75.5,
        "rooms": 2,
        "floor": 5,
        "total_floors": 12,
        "address": "ул. Тестовая, 1",
        "city": "Москва",
        "district": "Центральный",
        "metro_station": "Тестовая"
    }


@pytest.fixture
def sample_event_data():
    """Тестовые данные для события"""
    return {
        "title": "Показ квартиры",
        "description": "Показ тестовой квартиры",
        "event_type": "showing",
        "start_time": "2024-01-15T10:00:00",
        "end_time": "2024-01-15T11:00:00",
        "location": "ул. Тестовая, 1",
        "client_name": "Иван Иванов",
        "client_phone": "+79001234567",
        "client_email": "client@example.com",
        "notes": "Тестовые заметки"
    }


@pytest.fixture
def sample_user_data():
    """Тестовые данные для пользователя"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "phone": "+79001234567"
    }


# Утилиты для тестов
class TestUtils:
    """Утилиты для тестов"""
    
    @staticmethod
    async def create_test_user(db: AsyncSession, **kwargs) -> "User":
        """Создание тестового пользователя"""
        from app.models.user import User
        from app.core.auth import get_password_hash
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": get_password_hash("testpass123"),
            "full_name": "Test User",
            "is_active": True,
            "is_admin": False,
            **kwargs
        }
        
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def create_test_property(db: AsyncSession, user_id: int, **kwargs) -> "Property":
        """Создание тестового объекта недвижимости"""
        from app.models.property import Property, PropertyType, DealType, PropertyStatus
        
        property_data = {
            "user_id": user_id,
            "title": "Тестовая квартира",
            "description": "Описание тестовой квартиры",
            "property_type": PropertyType.APARTMENT,
            "deal_type": DealType.SALE,
            "price": 5000000.0,
            "area": 75.5,
            "rooms": 2,
            "floor": 5,
            "total_floors": 12,
            "address": "ул. Тестовая, 1",
            "city": "Москва",
            "district": "Центральный",
            "metro_station": "Тестовая",
            "status": PropertyStatus.ACTIVE,
            **kwargs
        }
        
        property_obj = Property(**property_data)
        db.add(property_obj)
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    
    @staticmethod
    async def create_test_event(db: AsyncSession, user_id: int, **kwargs) -> "CalendarEvent":
        """Создание тестового события"""
        from app.models.calendar import CalendarEvent, EventType, EventStatus
        from datetime import datetime, timedelta
        
        event_data = {
            "user_id": user_id,
            "title": "Показ квартиры",
            "description": "Показ тестовой квартиры",
            "event_type": EventType.SHOWING,
            "start_time": datetime.now() + timedelta(hours=1),
            "end_time": datetime.now() + timedelta(hours=2),
            "location": "ул. Тестовая, 1",
            "client_name": "Иван Иванов",
            "client_phone": "+79001234567",
            "client_email": "client@example.com",
            "status": EventStatus.SCHEDULED,
            **kwargs
        }
        
        event = CalendarEvent(**event_data)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
    
    @staticmethod
    async def get_auth_token(client: AsyncClient, username: str = "testuser", password: str = "testpass123") -> str:
        """Получение токена аутентификации"""
        login_data = {
            "username": username,
            "password": password
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        return response.json()["access_token"]
    
    @staticmethod
    def get_auth_headers(token: str) -> dict:
        """Получение заголовков с токеном"""
        return {"Authorization": f"Bearer {token}"}


# Фикстуры для утилит
@pytest.fixture
def test_utils():
    """Фикстура для утилит тестов"""
    return TestUtils


# Фикстуры для тестовых данных
@pytest.fixture
async def auth_user(db: AsyncSession, test_utils: TestUtils):
    """Создание аутентифицированного пользователя"""
    return await test_utils.create_test_user(db)


@pytest.fixture
async def auth_token(client: AsyncClient, auth_user, test_utils: TestUtils):
    """Получение токена для аутентифицированного пользователя"""
    return await test_utils.get_auth_token(client, auth_user.username, "testpass123")


@pytest.fixture
async def test_property(db: AsyncSession, auth_user, test_utils: TestUtils):
    """Создание тестового объекта недвижимости"""
    return await test_utils.create_test_property(db, auth_user.id)


@pytest.fixture
async def test_event(db: AsyncSession, auth_user, test_utils: TestUtils):
    """Создание тестового события"""
    return await test_utils.create_test_event(db, auth_user.id)


# Настройки для pytest
def pytest_configure(config):
    """Настройка pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов"""
    for item in items:
        # Добавляем маркеры по умолчанию
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration) 