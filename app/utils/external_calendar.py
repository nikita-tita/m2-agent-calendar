"""
Сервис интеграции с внешними календарями
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import pytz

from app.models.calendar import CalendarEvent
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExternalCalendarEvent:
    """Событие внешнего календаря"""
    id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees: List[str]
    calendar_type: str  # google, outlook


class ExternalCalendarService:
    """Сервис интеграции с внешними календарями"""
    
    def __init__(self):
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        
    async def create_event(self, event: CalendarEvent) -> Optional[str]:
        """Создание события во внешнем календаре"""
        try:
            # Определение типа календаря
            calendar_type = self._get_calendar_type(event)
            
            if calendar_type == "google":
                return await self._create_google_event(event)
            elif calendar_type == "outlook":
                return await self._create_outlook_event(event)
            else:
                logger.warning(f"Неизвестный тип календаря: {calendar_type}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка создания события во внешнем календаре: {e}")
            return None
    
    async def update_event(self, external_id: str, event: CalendarEvent) -> bool:
        """Обновление события во внешнем календаре"""
        try:
            calendar_type = self._get_calendar_type(event)
            
            if calendar_type == "google":
                return await self._update_google_event(external_id, event)
            elif calendar_type == "outlook":
                return await self._update_outlook_event(external_id, event)
            else:
                logger.warning(f"Неизвестный тип календаря: {calendar_type}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка обновления события во внешнем календаре: {e}")
            return False
    
    async def delete_event(self, external_id: str) -> bool:
        """Удаление события из внешнего календаря"""
        try:
            # Определение типа календаря по ID
            calendar_type = self._detect_calendar_type(external_id)
            
            if calendar_type == "google":
                return await self._delete_google_event(external_id)
            elif calendar_type == "outlook":
                return await self._delete_outlook_event(external_id)
            else:
                logger.warning(f"Неизвестный тип календаря: {calendar_type}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка удаления события из внешнего календаря: {e}")
            return False
    
    async def get_user_events(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        calendar_type: str = "google"
    ) -> List[ExternalCalendarEvent]:
        """Получение событий пользователя из внешнего календаря"""
        try:
            if calendar_type == "google":
                return await self._get_google_events(user_id, start_date, end_date)
            elif calendar_type == "outlook":
                return await self._get_outlook_events(user_id, start_date, end_date)
            else:
                logger.warning(f"Неизвестный тип календаря: {calendar_type}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения событий из внешнего календаря: {e}")
            return []
    
    async def check_availability(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        calendar_type: str = "google"
    ) -> bool:
        """Проверка доступности времени во внешнем календаре"""
        try:
            events = await self.get_user_events(user_id, start_time, end_time, calendar_type)
            
            # Проверка конфликтов
            for event in events:
                if (start_time < event.end_time and end_time > event.start_time):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки доступности во внешнем календаре: {e}")
            return True  # В случае ошибки считаем время доступным
    
    async def sync_events(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        calendar_type: str = "google"
    ) -> Dict[str, Any]:
        """Синхронизация событий с внешним календарем"""
        try:
            external_events = await self.get_user_events(user_id, start_date, end_date, calendar_type)
            
            # Здесь должна быть логика сравнения с локальными событиями
            # и создание/обновление/удаление событий
            
            sync_result = {
                "total_external_events": len(external_events),
                "created": 0,
                "updated": 0,
                "deleted": 0,
                "errors": 0
            }
            
            logger.info(f"Синхронизация завершена: {sync_result}")
            return sync_result
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации с внешним календарем: {e}")
            return {"error": str(e)}
    
    def _get_calendar_type(self, event: CalendarEvent) -> str:
        """Определение типа календаря для события"""
        if event.external_calendar_type:
            return event.external_calendar_type
        
        # Определение по настройкам пользователя
        if hasattr(event.user, 'calendar_settings'):
            if event.user.calendar_settings.google_calendar_enabled:
                return "google"
            elif event.user.calendar_settings.outlook_calendar_enabled:
                return "outlook"
        
        return "google"  # По умолчанию
    
    def _detect_calendar_type(self, external_id: str) -> str:
        """Определение типа календаря по ID события"""
        if external_id.startswith("google_"):
            return "google"
        elif external_id.startswith("outlook_"):
            return "outlook"
        else:
            # Попытка определить по формату ID
            if len(external_id) > 20 and "@" in external_id:
                return "google"
            else:
                return "outlook"
    
    async def _create_google_event(self, event: CalendarEvent) -> Optional[str]:
        """Создание события в Google Calendar"""
        try:
            # Здесь должна быть интеграция с Google Calendar API
            # Пока возвращаем заглушку
            
            event_data = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "location": event.location,
                "attendees": []
            }
            
            if event.client_name and event.client_phone:
                event_data["attendees"].append({
                    "email": f"{event.client_phone}@example.com",
                    "displayName": event.client_name
                })
            
            # Вызов Google Calendar API
            # external_id = await google_calendar_api.create_event(event_data)
            external_id = f"google_{event.id}_{datetime.now().timestamp()}"
            
            logger.info(f"Создано событие в Google Calendar: {external_id}")
            return external_id
            
        except Exception as e:
            logger.error(f"Ошибка создания события в Google Calendar: {e}")
            return None
    
    async def _update_google_event(self, external_id: str, event: CalendarEvent) -> bool:
        """Обновление события в Google Calendar"""
        try:
            event_data = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "location": event.location
            }
            
            # Вызов Google Calendar API
            # await google_calendar_api.update_event(external_id, event_data)
            
            logger.info(f"Обновлено событие в Google Calendar: {external_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления события в Google Calendar: {e}")
            return False
    
    async def _delete_google_event(self, external_id: str) -> bool:
        """Удаление события из Google Calendar"""
        try:
            # Вызов Google Calendar API
            # await google_calendar_api.delete_event(external_id)
            
            logger.info(f"Удалено событие из Google Calendar: {external_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления события из Google Calendar: {e}")
            return False
    
    async def _get_google_events(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[ExternalCalendarEvent]:
        """Получение событий из Google Calendar"""
        try:
            # Здесь должна быть интеграция с Google Calendar API
            # events_data = await google_calendar_api.list_events(start_date, end_date)
            
            # Заглушка для демонстрации
            events = []
            
            logger.info(f"Получено {len(events)} событий из Google Calendar")
            return events
            
        except Exception as e:
            logger.error(f"Ошибка получения событий из Google Calendar: {e}")
            return []
    
    async def _create_outlook_event(self, event: CalendarEvent) -> Optional[str]:
        """Создание события в Outlook Calendar"""
        try:
            # Здесь должна быть интеграция с Microsoft Graph API
            # Пока возвращаем заглушку
            
            event_data = {
                "subject": event.title,
                "body": {
                    "contentType": "text",
                    "content": event.description or ""
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "location": {
                    "displayName": event.location or ""
                }
            }
            
            # Вызов Microsoft Graph API
            # external_id = await outlook_calendar_api.create_event(event_data)
            external_id = f"outlook_{event.id}_{datetime.now().timestamp()}"
            
            logger.info(f"Создано событие в Outlook Calendar: {external_id}")
            return external_id
            
        except Exception as e:
            logger.error(f"Ошибка создания события в Outlook Calendar: {e}")
            return None
    
    async def _update_outlook_event(self, external_id: str, event: CalendarEvent) -> bool:
        """Обновление события в Outlook Calendar"""
        try:
            event_data = {
                "subject": event.title,
                "body": {
                    "contentType": "text",
                    "content": event.description or ""
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "Europe/Moscow"
                },
                "location": {
                    "displayName": event.location or ""
                }
            }
            
            # Вызов Microsoft Graph API
            # await outlook_calendar_api.update_event(external_id, event_data)
            
            logger.info(f"Обновлено событие в Outlook Calendar: {external_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления события в Outlook Calendar: {e}")
            return False
    
    async def _delete_outlook_event(self, external_id: str) -> bool:
        """Удаление события из Outlook Calendar"""
        try:
            # Вызов Microsoft Graph API
            # await outlook_calendar_api.delete_event(external_id)
            
            logger.info(f"Удалено событие из Outlook Calendar: {external_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления события из Outlook Calendar: {e}")
            return False
    
    async def _get_outlook_events(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[ExternalCalendarEvent]:
        """Получение событий из Outlook Calendar"""
        try:
            # Здесь должна быть интеграция с Microsoft Graph API
            # events_data = await outlook_calendar_api.list_events(start_date, end_date)
            
            # Заглушка для демонстрации
            events = []
            
            logger.info(f"Получено {len(events)} событий из Outlook Calendar")
            return events
            
        except Exception as e:
            logger.error(f"Ошибка получения событий из Outlook Calendar: {e}")
            return []
    
    async def setup_google_calendar_integration(self, user_id: int, auth_code: str) -> bool:
        """Настройка интеграции с Google Calendar"""
        try:
            # Здесь должна быть логика OAuth2 авторизации
            # и сохранение токенов доступа
            
            logger.info(f"Настроена интеграция с Google Calendar для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки интеграции с Google Calendar: {e}")
            return False
    
    async def setup_outlook_calendar_integration(self, user_id: int, auth_code: str) -> bool:
        """Настройка интеграции с Outlook Calendar"""
        try:
            # Здесь должна быть логика OAuth2 авторизации
            # и сохранение токенов доступа
            
            logger.info(f"Настроена интеграция с Outlook Calendar для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки интеграции с Outlook Calendar: {e}")
            return False
    
    async def get_calendar_list(self, user_id: int, calendar_type: str = "google") -> List[Dict[str, Any]]:
        """Получение списка календарей пользователя"""
        try:
            if calendar_type == "google":
                # return await google_calendar_api.list_calendars()
                return [
                    {"id": "primary", "name": "Основной календарь"},
                    {"id": "work", "name": "Рабочий календарь"}
                ]
            elif calendar_type == "outlook":
                # return await outlook_calendar_api.list_calendars()
                return [
                    {"id": "default", "name": "Основной календарь"},
                    {"id": "work", "name": "Рабочий календарь"}
                ]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения списка календарей: {e}")
            return [] 