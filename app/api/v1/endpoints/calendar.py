"""
API endpoints для управления календарем и событиями
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.database import get_async_session
from app.models.calendar import CalendarEvent, EventType, EventStatus
from app.models.user import User
from app.schemas.calendar import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventFilter,
    EventConflict
)
from app.services.calendar_service import CalendarService
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/events", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Создание нового события"""
    try:
        calendar_service = CalendarService(db)
        
        # Проверяем конфликты
        conflicts = await calendar_service.check_conflicts(
            user_id=current_user.id,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            exclude_event_id=None
        )
        
        if conflicts:
            raise HTTPException(
                status_code=409,
                detail=f"Обнаружен конфликт времени: {conflicts[0].title}"
            )
        
        # Создаем событие
        event = await calendar_service.create_event(
            user_id=current_user.id,
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            location=event_data.location,
            client_name=event_data.client_name,
            client_phone=event_data.client_phone,
            client_email=event_data.client_email,
            property_id=event_data.property_id,
            reminder_time=event_data.reminder_time,
            notes=event_data.notes
        )
        
        logger.info(f"Created event {event.id} for user {current_user.id}")
        
        return EventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания события")


@router.get("/events", response_model=EventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[EventType] = None,
    status: Optional[EventStatus] = None,
    client_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение списка событий с фильтрацией"""
    try:
        calendar_service = CalendarService(db)
        
        # Получаем события
        events = await calendar_service.get_events(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            status=status,
            client_name=client_name,
            skip=skip,
            limit=limit
        )
        
        # Подсчитываем общее количество
        total = await calendar_service.count_events(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            status=status,
            client_name=client_name
        )
        
        return EventListResponse(
            events=[EventResponse.from_orm(event) for event in events],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения событий")


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение конкретного события"""
    try:
        calendar_service = CalendarService(db)
        
        event = await calendar_service.get_event(event_id, current_user.id)
        
        if not event:
            raise HTTPException(status_code=404, detail="Событие не найдено")
        
        return EventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения события")


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Обновление события"""
    try:
        calendar_service = CalendarService(db)
        
        # Проверяем, что событие существует и принадлежит пользователю
        existing_event = await calendar_service.get_event(event_id, current_user.id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Событие не найдено")
        
        # Проверяем конфликты, если изменилось время
        if event_data.start_time or event_data.end_time:
            start_time = event_data.start_time or existing_event.start_time
            end_time = event_data.end_time or existing_event.end_time
            
            conflicts = await calendar_service.check_conflicts(
                user_id=current_user.id,
                start_time=start_time,
                end_time=end_time,
                exclude_event_id=event_id
            )
            
            if conflicts:
                raise HTTPException(
                    status_code=409,
                    detail=f"Обнаружен конфликт времени: {conflicts[0].title}"
                )
        
        # Обновляем событие
        updated_event = await calendar_service.update_event(
            event_id=event_id,
            user_id=current_user.id,
            **event_data.dict(exclude_unset=True)
        )
        
        logger.info(f"Updated event {event_id} for user {current_user.id}")
        
        return EventResponse.from_orm(updated_event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления события")


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Удаление события"""
    try:
        calendar_service = CalendarService(db)
        
        # Проверяем, что событие существует и принадлежит пользователю
        existing_event = await calendar_service.get_event(event_id, current_user.id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Событие не найдено")
        
        # Удаляем событие
        await calendar_service.delete_event(event_id, current_user.id)
        
        logger.info(f"Deleted event {event_id} for user {current_user.id}")
        
        return {"message": "Событие успешно удалено"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления события")


@router.post("/events/{event_id}/status")
async def change_event_status(
    event_id: int,
    status: EventStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Изменение статуса события"""
    try:
        calendar_service = CalendarService(db)
        
        # Проверяем, что событие существует и принадлежит пользователю
        existing_event = await calendar_service.get_event(event_id, current_user.id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Событие не найдено")
        
        # Изменяем статус
        updated_event = await calendar_service.update_event(
            event_id=event_id,
            user_id=current_user.id,
            status=status
        )
        
        logger.info(f"Changed status of event {event_id} to {status} for user {current_user.id}")
        
        return {"message": f"Статус изменен на {status.value}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing status of event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения статуса")


@router.get("/events/conflicts")
async def check_conflicts(
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Проверка конфликтов времени"""
    try:
        calendar_service = CalendarService(db)
        
        conflicts = await calendar_service.check_conflicts(
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            exclude_event_id=exclude_event_id
        )
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": [EventConflict.from_orm(conflict) for conflict in conflicts]
        }
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {e}")
        raise HTTPException(status_code=500, detail="Ошибка проверки конфликтов")


@router.get("/events/suggestions")
async def get_event_suggestions(
    date: Optional[datetime] = None,
    event_type: Optional[EventType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение предложений по времени для событий"""
    try:
        calendar_service = CalendarService(db)
        
        if not date:
            date = datetime.now()
        
        suggestions = await calendar_service.get_time_suggestions(
            user_id=current_user.id,
            date=date,
            event_type=event_type
        )
        
        return {
            "date": date,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting event suggestions: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения предложений")


@router.get("/events/statistics")
async def get_event_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение статистики событий"""
    try:
        calendar_service = CalendarService(db)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        stats = await calendar_service.get_event_statistics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting event statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.get("/events/upcoming")
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение предстоящих событий"""
    try:
        calendar_service = CalendarService(db)
        
        end_date = datetime.now() + timedelta(days=days)
        
        events = await calendar_service.get_events(
            user_id=current_user.id,
            start_date=datetime.now(),
            end_date=end_date,
            status=EventStatus.SCHEDULED
        )
        
        return {
            "days": days,
            "events": [EventResponse.from_orm(event) for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения предстоящих событий")


@router.get("/events/today")
async def get_today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение событий на сегодня"""
    try:
        calendar_service = CalendarService(db)
        
        today = datetime.now().date()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        
        events = await calendar_service.get_events(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "date": today,
            "events": [EventResponse.from_orm(event) for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error getting today events: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения событий на сегодня")


@router.post("/events/bulk")
async def bulk_create_events(
    events_data: List[EventCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Массовое создание событий"""
    try:
        calendar_service = CalendarService(db)
        
        created_events = []
        errors = []
        
        for i, event_data in enumerate(events_data):
            try:
                # Проверяем конфликты
                conflicts = await calendar_service.check_conflicts(
                    user_id=current_user.id,
                    start_time=event_data.start_time,
                    end_time=event_data.end_time,
                    exclude_event_id=None
                )
                
                if conflicts:
                    errors.append({
                        "index": i,
                        "error": f"Конфликт времени: {conflicts[0].title}"
                    })
                    continue
                
                # Создаем событие
                event = await calendar_service.create_event(
                    user_id=current_user.id,
                    title=event_data.title,
                    description=event_data.description,
                    event_type=event_data.event_type,
                    start_time=event_data.start_time,
                    end_time=event_data.end_time,
                    location=event_data.location,
                    client_name=event_data.client_name,
                    client_phone=event_data.client_phone,
                    client_email=event_data.client_email,
                    property_id=event_data.property_id,
                    reminder_time=event_data.reminder_time,
                    notes=event_data.notes
                )
                
                created_events.append(EventResponse.from_orm(event))
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e)
                })
        
        return {
            "created_events": created_events,
            "total_created": len(created_events),
            "total_requested": len(events_data),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error bulk creating events: {e}")
        raise HTTPException(status_code=500, detail="Ошибка массового создания событий")


@router.get("/export")
async def export_calendar(
    format: str = Query("ics", pattern="^(ics|json|csv)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Экспорт календаря"""
    try:
        # Валидация формата
        if format not in ["ics", "json", "csv"]:
            raise HTTPException(status_code=400, detail="Неверный формат экспорта")
        
        calendar_service = CalendarService(db)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now() + timedelta(days=30)
        
        # Экспортируем календарь
        export_data = await calendar_service.export_calendar(
            user_id=current_user.id,
            format=format,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting calendar: {e}")
        raise HTTPException(status_code=500, detail="Ошибка экспорта календаря") 