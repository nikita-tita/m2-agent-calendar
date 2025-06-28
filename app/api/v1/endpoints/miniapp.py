"""
API endpoints для Telegram Mini App
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_async_session
from app.models.user import User
from app.models.event import Event
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)
router = APIRouter()

class MiniAppEventCreate(BaseModel):
    """Схема для создания события через Mini App"""
    title: str
    date: str
    time: str
    duration: int = 60
    type: str = "meeting"
    location: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    reminder: bool = True

@router.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    """Отдаём HTML страницу Mini App"""
    try:
        with open("miniapp/main.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Mini App not found")

@router.get("/static/css/{file_name}")
async def serve_css(file_name: str):
    """Отдаём CSS файлы"""
    try:
        return FileResponse(f"miniapp/static/css/{file_name}", media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSS file not found")

@router.get("/static/js/{file_name}")
async def serve_js(file_name: str):
    """Отдаём JavaScript файлы"""
    try:
        return FileResponse(f"miniapp/static/js/{file_name}", media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JavaScript file not found")

@router.get("/events")
async def get_miniapp_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: int = 1,  # Временно для демонстрации
    session: AsyncSession = Depends(get_async_session)
):
    """Получение событий для Mini App"""
    try:
        # Парсим даты
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)
            
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now() + timedelta(days=30)
        
        # Получаем события из базы
        from sqlalchemy import select
        result = await session.execute(
            select(Event).where(
                Event.user_id == user_id,
                Event.start_time >= start,
                Event.start_time <= end
            ).order_by(Event.start_time)
        )
        events = result.scalars().all()
        
        # Форматируем для Mini App
        formatted_events = []
        for event in events:
            formatted_events.append({
                "id": event.id,
                "title": event.title,
                "date": event.start_time.date().isoformat(),
                "time": event.start_time.time().strftime("%H:%M"),
                "type": event.event_type,
                "location": event.location,
                "client_name": getattr(event, 'client_name', None),
                "description": event.description,
                "duration": int((event.end_time - event.start_time).total_seconds() / 60)
            })
        
        return {
            "status": "success",
            "events": formatted_events
        }
        
    except Exception as e:
        logger.error(f"Error getting Mini App events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get events")

@router.post("/events")
async def create_miniapp_event(
    event_data: MiniAppEventCreate,
    user_id: int = 1,  # Временно для демонстрации
    session: AsyncSession = Depends(get_async_session)
):
    """Создание события через Mini App"""
    try:
        # Парсим дату и время
        event_datetime = datetime.fromisoformat(f"{event_data.date}T{event_data.time}")
        end_datetime = event_datetime + timedelta(minutes=event_data.duration)
        
        # Создаём событие
        from app.models.event import EventType, EventStatus, CreatedFrom
        
        event = Event(
            user_id=user_id,
            title=event_data.title,
            description=event_data.description,
            start_time=event_datetime,
            end_time=end_datetime,
            event_type=EventType(event_data.type),
            status=EventStatus.ACTIVE,
            created_from=CreatedFrom.API,
            location=event_data.location,
            is_reminder_sent=False
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        return {
            "status": "success",
            "event_id": event.id,
            "message": "Событие создано успешно"
        }
        
    except Exception as e:
        logger.error(f"Error creating Mini App event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")

@router.delete("/events/{event_id}")
async def delete_miniapp_event(
    event_id: int,
    user_id: int = 1,  # Временно для демонстрации
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление события через Mini App"""
    try:
        from sqlalchemy import select
        
        result = await session.execute(
            select(Event).where(Event.id == event_id, Event.user_id == user_id)
        )
        event = result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        await session.delete(event)
        await session.commit()
        
        return {
            "status": "success",
            "message": "Событие удалено успешно"
        }
        
    except Exception as e:
        logger.error(f"Error deleting Mini App event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete event")

@router.post("/sync")
async def sync_miniapp_events(
    user_id: int = 1,  # Временно для демонстрации
    session: AsyncSession = Depends(get_async_session)
):
    """Синхронизация событий Mini App"""
    try:
        # Имитация синхронизации
        await asyncio.sleep(1)
        
        return {
            "status": "success",
            "message": "События синхронизированы",
            "synced_count": 0
        }
        
    except Exception as e:
        logger.error(f"Error syncing Mini App events: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync events")
