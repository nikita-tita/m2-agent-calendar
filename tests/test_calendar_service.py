"""
Тесты для сервиса календаря
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytz

from app.services.calendar_service import CalendarService, CalendarConflictError, EventValidationError
from app.models.calendar import CalendarEvent, EventType, EventStatus
from app.models.user import User


@pytest.fixture
def mock_db():
    """Мок базы данных"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def calendar_service(mock_db):
    """Сервис календаря с мок базы данных"""
    return CalendarService(mock_db)


@pytest.fixture
def sample_user():
    """Тестовый пользователь"""
    user = User(
        id=1,
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    return user


@pytest.fixture
def sample_event_data():
    """Тестовые данные события"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    start_time = datetime.now(moscow_tz) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)
    
    return {
        "user_id": 1,
        "event_type": EventType.MEETING,
        "title": "Тестовая встреча",
        "description": "Описание тестовой встречи",
        "start_time": start_time,
        "end_time": end_time,
        "location": "Тестовый адрес",
        "client_name": "Тестовый клиент",
        "client_phone": "+79001234567"
    }


class TestCalendarService:
    """Тесты для CalendarService"""
    
    async def test_create_event_success(self, calendar_service, mock_db, sample_event_data):
        """Тест успешного создания события"""
        # Настройка моков
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        # Создание события
        event = await calendar_service.create_event(**sample_event_data)
        
        # Проверки
        assert event is not None
        assert event.title == sample_event_data["title"]
        assert event.event_type == sample_event_data["event_type"]
        assert event.user_id == sample_event_data["user_id"]
        assert event.status == EventStatus.SCHEDULED
        
        # Проверка вызовов
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    async def test_create_event_validation_error(self, calendar_service, sample_event_data):
        """Тест ошибки валидации при создании события"""
        # Неверное время (конец раньше начала)
        sample_event_data["start_time"] = datetime.now() + timedelta(hours=2)
        sample_event_data["end_time"] = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(EventValidationError, match="Время начала должно быть раньше времени окончания"):
            await calendar_service.create_event(**sample_event_data)
    
    async def test_create_event_past_time_error(self, calendar_service, sample_event_data):
        """Тест ошибки создания события в прошлом"""
        # Время в прошлом
        sample_event_data["start_time"] = datetime.now() - timedelta(hours=2)
        sample_event_data["end_time"] = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(EventValidationError, match="Нельзя создавать события в прошлом"):
            await calendar_service.create_event(**sample_event_data)
    
    async def test_create_event_conflict_error(self, calendar_service, mock_db, sample_event_data):
        """Тест ошибки конфликта при создании события"""
        # Настройка мока для возврата конфликтующего события
        conflict_event = CalendarEvent(
            id=1,
            user_id=sample_event_data["user_id"],
            event_type=EventType.MEETING,
            title="Конфликтующее событие",
            start_time=sample_event_data["start_time"],
            end_time=sample_event_data["end_time"],
            status=EventStatus.SCHEDULED
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [conflict_event]
        
        with pytest.raises(CalendarConflictError, match="Найдено 1 конфликтующих событий"):
            await calendar_service.create_event(**sample_event_data)
    
    async def test_get_user_events(self, calendar_service, mock_db):
        """Тест получения событий пользователя"""
        # Настройка моков
        events = [
            CalendarEvent(
                id=1,
                user_id=1,
                event_type=EventType.MEETING,
                title="Событие 1",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=1),
                status=EventStatus.SCHEDULED
            ),
            CalendarEvent(
                id=2,
                user_id=1,
                event_type=EventType.SHOWING,
                title="Событие 2",
                start_time=datetime.now() + timedelta(hours=2),
                end_time=datetime.now() + timedelta(hours=3),
                status=EventStatus.SCHEDULED
            )
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = events
        
        # Получение событий
        result = await calendar_service.get_user_events(user_id=1)
        
        # Проверки
        assert len(result) == 2
        assert result[0].title == "Событие 1"
        assert result[1].title == "Событие 2"
        
        # Проверка вызова
        mock_db.execute.assert_called_once()
    
    async def test_get_today_events(self, calendar_service, mock_db):
        """Тест получения событий на сегодня"""
        # Настройка моков
        today_events = [
            CalendarEvent(
                id=1,
                user_id=1,
                event_type=EventType.MEETING,
                title="Сегодняшнее событие",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=1),
                status=EventStatus.SCHEDULED
            )
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = today_events
        
        # Получение событий
        result = await calendar_service.get_today_events(user_id=1)
        
        # Проверки
        assert len(result) == 1
        assert result[0].title == "Сегодняшнее событие"
    
    async def test_get_upcoming_events(self, calendar_service, mock_db):
        """Тест получения предстоящих событий"""
        # Настройка моков
        upcoming_events = [
            CalendarEvent(
                id=1,
                user_id=1,
                event_type=EventType.MEETING,
                title="Предстоящее событие",
                start_time=datetime.now() + timedelta(days=1),
                end_time=datetime.now() + timedelta(days=1, hours=1),
                status=EventStatus.SCHEDULED
            )
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = upcoming_events
        
        # Получение событий
        result = await calendar_service.get_upcoming_events(user_id=1, days=7)
        
        # Проверки
        assert len(result) == 1
        assert result[0].title == "Предстоящее событие"
    
    async def test_suggest_meeting_times(self, calendar_service, mock_db):
        """Тест предложения времени для встречи"""
        # Настройка моков
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        # Параметры для предложения времени
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)
        
        # Получение предложений
        suggestions = await calendar_service.suggest_meeting_times(
            user_id=1,
            duration_minutes=60,
            start_date=start_date,
            end_date=end_date
        )
        
        # Проверки
        assert len(suggestions) > 0
        assert all(s.confidence > 0 for s in suggestions)
        assert all(s.start_time < s.end_time for s in suggestions)
    
    async def test_check_availability(self, calendar_service, mock_db):
        """Тест проверки доступности времени"""
        # Настройка моков для свободного времени
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        # Проверка доступности
        is_available = await calendar_service.check_availability(
            user_id=1,
            start_time=start_time,
            end_time=end_time
        )
        
        # Проверки
        assert is_available is True
    
    async def test_check_availability_conflict(self, calendar_service, mock_db):
        """Тест проверки доступности при конфликте"""
        # Настройка моков для занятого времени
        conflict_event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Конфликтующее событие",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            status=EventStatus.SCHEDULED
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [conflict_event]
        
        start_time = datetime.now() + timedelta(hours=1, minutes=30)
        end_time = start_time + timedelta(hours=1)
        
        # Проверка доступности
        is_available = await calendar_service.check_availability(
            user_id=1,
            start_time=start_time,
            end_time=end_time
        )
        
        # Проверки
        assert is_available is False
    
    async def test_get_calendar_stats(self, calendar_service, mock_db):
        """Тест получения статистики календаря"""
        # Настройка моков
        events = [
            CalendarEvent(
                id=1,
                user_id=1,
                event_type=EventType.MEETING,
                title="Завершенное событие",
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now() - timedelta(days=1, hours=-1),
                status=EventStatus.COMPLETED
            ),
            CalendarEvent(
                id=2,
                user_id=1,
                event_type=EventType.SHOWING,
                title="Предстоящее событие",
                start_time=datetime.now() + timedelta(days=1),
                end_time=datetime.now() + timedelta(days=1, hours=1),
                status=EventStatus.SCHEDULED
            )
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = events
        
        # Получение статистики
        stats = await calendar_service.get_calendar_stats(user_id=1, days=30)
        
        # Проверки
        assert stats["total_events"] == 2
        assert stats["completed_events"] == 1
        assert stats["upcoming_events"] == 1
        assert "meeting" in stats["events_by_type"]
        assert "showing" in stats["events_by_type"]
    
    async def test_update_event_success(self, calendar_service, mock_db):
        """Тест успешного обновления события"""
        # Настройка моков
        existing_event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Старое название",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            status=EventStatus.SCHEDULED
        )
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_event
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        # Обновление события
        updated_event = await calendar_service.update_event(
            event_id=1,
            user_id=1,
            title="Новое название"
        )
        
        # Проверки
        assert updated_event.title == "Новое название"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    async def test_update_event_not_found(self, calendar_service, mock_db):
        """Тест обновления несуществующего события"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Попытка обновления
        with pytest.raises(EventValidationError, match="Событие не найдено"):
            await calendar_service.update_event(
                event_id=999,
                user_id=1,
                title="Новое название"
            )
    
    async def test_delete_event_success(self, calendar_service, mock_db):
        """Тест успешного удаления события"""
        # Настройка моков
        existing_event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Событие для удаления",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            status=EventStatus.SCHEDULED
        )
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_event
        
        # Удаление события
        result = await calendar_service.delete_event(event_id=1, user_id=1)
        
        # Проверки
        assert result is True
        mock_db.delete.assert_called_once_with(existing_event)
        mock_db.commit.assert_called_once()
    
    async def test_delete_event_not_found(self, calendar_service, mock_db):
        """Тест удаления несуществующего события"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Попытка удаления
        result = await calendar_service.delete_event(event_id=999, user_id=1)
        
        # Проверки
        assert result is False
        mock_db.delete.assert_not_called()


class TestEventValidation:
    """Тесты валидации событий"""
    
    async def test_event_duration_property(self):
        """Тест свойства продолжительности события"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2, minutes=30)
        
        event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Тестовое событие",
            start_time=start_time,
            end_time=end_time,
            status=EventStatus.SCHEDULED
        )
        
        assert event.duration_minutes == 150  # 2 часа 30 минут
    
    async def test_event_is_overdue_property(self):
        """Тест свойства просроченности события"""
        # Событие в прошлом
        past_event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Просроченное событие",
            start_time=datetime.now() - timedelta(hours=2),
            end_time=datetime.now() - timedelta(hours=1),
            status=EventStatus.SCHEDULED
        )
        
        # Событие в будущем
        future_event = CalendarEvent(
            id=2,
            user_id=1,
            event_type=EventType.MEETING,
            title="Будущее событие",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            status=EventStatus.SCHEDULED
        )
        
        assert past_event.is_overdue is True
        assert future_event.is_overdue is False
    
    async def test_event_is_today_property(self):
        """Тест свойства события сегодня"""
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = start_time + timedelta(hours=1)
        
        today_event = CalendarEvent(
            id=1,
            user_id=1,
            event_type=EventType.MEETING,
            title="Сегодняшнее событие",
            start_time=start_time,
            end_time=end_time,
            status=EventStatus.SCHEDULED
        )
        
        assert today_event.is_today is True 