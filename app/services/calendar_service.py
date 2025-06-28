"""
Сервис календаря
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, date

from app.models.event import Event
from app.models.user import User


class CalendarService:
    """Сервис для работы с календарем"""
    
    @staticmethod
    async def get_user_events(
        user_id: int,
        session: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Event]:
        """Получить события пользователя"""
        
        query = select(Event).where(Event.user_id == user_id)
        
        if start_date:
            query = query.where(Event.date >= start_date)
        if end_date:
            query = query.where(Event.date <= end_date)
            
        query = query.order_by(Event.date, Event.time)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_event(
        user_id: int,
        title: str,
        date: str,
        time: str,
        description: str,
        session: AsyncSession
    ) -> Event:
        """Создать новое событие"""
        
        new_event = Event(
            user_id=user_id,
            title=title,
            date=date,
            time=time,
            description=description,
            created_at=datetime.utcnow()
        )
        
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)
        
        return new_event
    
    @staticmethod
    async def update_event(
        event_id: int,
        user_id: int,
        updates: dict,
        session: AsyncSession
    ) -> Optional[Event]:
        """Обновить событие"""
        
        query = select(Event).where(
            Event.id == event_id,
            Event.user_id == user_id
        )
        
        result = await session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return None
        
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        event.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(event)
        
        return event
    
    @staticmethod
    async def delete_event(
        event_id: int,
        user_id: int,
        session: AsyncSession
    ) -> bool:
        """Удалить событие"""
        
        query = select(Event).where(
            Event.id == event_id,
            Event.user_id == user_id
        )
        
        result = await session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return False
        
        await session.delete(event)
        await session.commit()
        
        return True
    
    @staticmethod
    async def get_event_by_id(
        event_id: int,
        user_id: int,
        session: AsyncSession
    ) -> Optional[Event]:
        """Получить событие по ID"""
        
        query = select(Event).where(
            Event.id == event_id,
            Event.user_id == user_id
        )
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
