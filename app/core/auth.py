"""
Система аутентификации для API
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)

# Настройка безопасности
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """Получение текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Получаем пользователя из базы данных
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получение активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неактивный пользователь"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получение администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user


class AuthService:
    """Сервис аутентификации"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            # Ищем пользователя по username или email
            query = select(User).where(
                (User.username == username) | (User.email == username)
            )
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if not verify_password(password, user.password_hash):
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        is_admin: bool = False
    ) -> Optional[User]:
        """Создание нового пользователя"""
        try:
            # Проверяем, что пользователь не существует
            existing_user_query = select(User).where(
                (User.username == username) | (User.email == email)
            )
            result = await self.db.execute(existing_user_query)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                return None
            
            # Создаем нового пользователя
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                full_name=full_name,
                phone=phone,
                is_admin=is_admin,
                is_active=True
            )
            
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            return new_user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await self.db.rollback()
            return None
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Изменение пароля пользователя"""
        try:
            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Проверяем текущий пароль
            if not verify_password(current_password, user.password_hash):
                return False
            
            # Обновляем пароль
            user.password_hash = get_password_hash(new_password)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            await self.db.rollback()
            return False
    
    async def reset_password(self, email: str) -> bool:
        """Сброс пароля"""
        try:
            # Получаем пользователя по email
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Генерируем временный пароль
            import secrets
            import string
            
            temp_password = ''.join(
                secrets.choice(string.ascii_letters + string.digits)
                for _ in range(12)
            )
            
            # Обновляем пароль
            user.password_hash = get_password_hash(temp_password)
            await self.db.commit()
            
            # Здесь должна быть отправка email с временным паролем
            logger.info(f"Temporary password for {email}: {temp_password}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            await self.db.rollback()
            return False
    
    async def update_user_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[User]:
        """Обновление профиля пользователя"""
        try:
            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Обновляем поля
            if full_name is not None:
                user.full_name = full_name
            if phone is not None:
                user.phone = phone
            if email is not None:
                # Проверяем, что email не занят
                if email != user.email:
                    existing_email_query = select(User).where(User.email == email)
                    email_result = await self.db.execute(existing_email_query)
                    existing_email_user = email_result.scalar_one_or_none()
                    
                    if existing_email_user:
                        return None
                    
                    user.email = email
            
            await self.db.commit()
            await self.db.refresh(user)
            
            return user
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            await self.db.rollback()
            return None
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Деактивация пользователя"""
        try:
            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Деактивируем пользователя
            user.is_active = False
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            await self.db.rollback()
            return False
    
    async def activate_user(self, user_id: int) -> bool:
        """Активация пользователя"""
        try:
            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Активируем пользователя
            user.is_active = True
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            await self.db.rollback()
            return False 