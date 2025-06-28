"""
Тесты для API аутентификации
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_async_session
from app.models.user import User
from app.core.auth import get_password_hash


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Создание тестового пользователя"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    """Создание тестового администратора"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


class TestAuthAPI:
    """Тесты для API аутентификации"""
    
    async def test_register_user_success(self, client: AsyncClient):
        """Тест успешной регистрации пользователя"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "phone": "+79001234567"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["phone"] == user_data["phone"]
        assert data["is_active"] is True
        assert data["is_admin"] is False
        assert "password" not in data
    
    async def test_register_user_duplicate_username(self, client: AsyncClient, test_user: User):
        """Тест регистрации с существующим username"""
        user_data = {
            "username": test_user.username,
            "email": "another@example.com",
            "password": "newpass123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]
    
    async def test_register_user_duplicate_email(self, client: AsyncClient, test_user: User):
        """Тест регистрации с существующим email"""
        user_data = {
            "username": "anotheruser",
            "email": test_user.email,
            "password": "newpass123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]
    
    async def test_register_user_invalid_data(self, client: AsyncClient):
        """Тест регистрации с некорректными данными"""
        user_data = {
            "username": "a",  # слишком короткий
            "email": "invalid-email",
            "password": "123"  # слишком короткий
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Тест успешного входа"""
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    async def test_login_with_email(self, client: AsyncClient, test_user: User):
        """Тест входа с email"""
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Тест входа с неверными данными"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Неверное имя пользователя или пароль" in response.json()["detail"]
    
    async def test_login_inactive_user(self, client: AsyncClient, db: AsyncSession):
        """Тест входа неактивного пользователя"""
        # Создаем неактивного пользователя
        user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=get_password_hash("testpass123"),
            is_active=False
        )
        db.add(user)
        await db.commit()
        
        login_data = {
            "username": user.username,
            "password": "testpass123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 400
        assert "Неактивный пользователь" in response.json()["detail"]
    
    async def test_login_telegram_success(self, client: AsyncClient, db: AsyncSession):
        """Тест успешной аутентификации через Telegram"""
        telegram_data = {
            "telegram_id": 123456789,
            "username": "telegram_user",
            "first_name": "Telegram",
            "last_name": "User"
        }
        
        response = await client.post("/api/v1/auth/login/telegram", json=telegram_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_telegram_existing_user(self, client: AsyncClient, db: AsyncSession):
        """Тест аутентификации через Telegram существующего пользователя"""
        # Создаем пользователя с Telegram ID
        user = User(
            username="telegram_existing",
            email="telegram@example.com",
            password_hash="",
            telegram_id=987654321,
            is_active=True
        )
        db.add(user)
        await db.commit()
        
        telegram_data = {
            "telegram_id": 987654321,
            "username": "telegram_existing"
        }
        
        response = await client.post("/api/v1/auth/login/telegram", json=telegram_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    async def test_get_current_user(self, client: AsyncClient, test_user: User):
        """Тест получения информации о текущем пользователе"""
        # Сначала получаем токен
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Получаем информацию о пользователе
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Тест получения информации с неверным токеном"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    async def test_update_current_user(self, client: AsyncClient, test_user: User):
        """Тест обновления профиля пользователя"""
        # Получаем токен
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Обновляем профиль
        update_data = {
            "full_name": "Updated Name",
            "phone": "+79009876543"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.put("/api/v1/auth/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["phone"] == update_data["phone"]
    
    async def test_change_password_success(self, client: AsyncClient, test_user: User):
        """Тест успешной смены пароля"""
        # Получаем токен
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Меняем пароль
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpassword123"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        assert "успешно изменен" in response.json()["message"]
    
    async def test_change_password_wrong_current(self, client: AsyncClient, test_user: User):
        """Тест смены пароля с неверным текущим паролем"""
        # Получаем токен
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Меняем пароль с неверным текущим
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpassword123"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 400
        assert "Неверный текущий пароль" in response.json()["detail"]
    
    async def test_reset_password(self, client: AsyncClient, test_user: User):
        """Тест сброса пароля"""
        reset_data = {
            "email": test_user.email
        }
        
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        assert "отправлены на email" in response.json()["message"]
    
    async def test_reset_password_nonexistent_email(self, client: AsyncClient):
        """Тест сброса пароля с несуществующим email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = await client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        """Тест обновления токена"""
        # Получаем токен
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Обновляем токен
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/v1/auth/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    async def test_get_users_admin(self, client: AsyncClient, admin_user: User):
        """Тест получения списка пользователей администратором"""
        # Получаем токен администратора
        login_data = {
            "username": admin_user.username,
            "password": "adminpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Получаем список пользователей
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    async def test_get_users_non_admin(self, client: AsyncClient, test_user: User):
        """Тест получения списка пользователей не-администратором"""
        # Получаем токен обычного пользователя
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Пытаемся получить список пользователей
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/users", headers=headers)
        
        assert response.status_code == 403
        assert "Недостаточно прав" in response.json()["detail"]
    
    async def test_activate_user_admin(self, client: AsyncClient, admin_user: User, db: AsyncSession):
        """Тест активации пользователя администратором"""
        # Создаем неактивного пользователя
        inactive_user = User(
            username="inactive_user",
            email="inactive@example.com",
            password_hash=get_password_hash("testpass123"),
            is_active=False
        )
        db.add(inactive_user)
        await db.commit()
        
        # Получаем токен администратора
        login_data = {
            "username": admin_user.username,
            "password": "adminpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Активируем пользователя
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(f"/api/v1/auth/users/{inactive_user.id}/activate", headers=headers)
        
        assert response.status_code == 200
        assert "активирован" in response.json()["message"]
    
    async def test_deactivate_user_admin(self, client: AsyncClient, admin_user: User, test_user: User):
        """Тест деактивации пользователя администратором"""
        # Получаем токен администратора
        login_data = {
            "username": admin_user.username,
            "password": "adminpass123"
        }
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Деактивируем пользователя
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(f"/api/v1/auth/users/{test_user.id}/deactivate", headers=headers)
        
        assert response.status_code == 200
        assert "деактивирован" in response.json()["message"] 