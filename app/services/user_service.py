"""
Упрощённый сервис пользователей
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.user import User

async def get_or_create_user(
    telegram_id: int,
    username: Optional[str],
    session: AsyncSession,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """Получение или создание пользователя"""
    
    # Ищем существующего пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Создаём нового пользователя
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user 