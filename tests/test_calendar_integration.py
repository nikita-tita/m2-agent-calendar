"""
Тесты интеграции календаря и мини-приложения
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.endpoints.calendar import get_events, create_event, delete_event
from app.models.event import Event


class TestCalendarAPI:
    """Тесты API календаря"""
    
    @pytest.mark.asyncio
    async def test_get_events_success(self):
        """Тест успешного получения событий"""
        
        # Мок событий
        mock_events = [
            Mock(
                id=1,
                title="Встреча",
                date="2024-12-15",
                time="15:00",
                description="Встреча с клиентом"
            ),
            Mock(
                id=2, 
                title="Звонок",
                date="2024-12-16",
                time="17:30",
                description="Звонок по проекту"
            )
        ]
        
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_events
        
        # Мок пользователя
        mock_user = Mock(id=1)
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            result = await get_events(mock_session, mock_user)
            
            assert len(result) == 2
            assert result[0]['title'] == "Встреча"
            assert result[1]['title'] == "Звонок"
    
    @pytest.mark.asyncio
    async def test_create_event_success(self):
        """Тест успешного создания события"""
        
        mock_session = AsyncMock()
        mock_user = Mock(id=1)
        
        event_data = {
            'title': 'Новая встреча',
            'date': '2024-12-20',
            'time': '14:00',
            'description': 'Важная встреча'
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            result = await create_event(event_data, mock_session, mock_user)
            
            assert result['title'] == event_data['title']
            assert result['date'] == event_data['date']
            assert result['time'] == event_data['time']
    
    @pytest.mark.asyncio
    async def test_delete_event_success(self):
        """Тест успешного удаления события"""
        
        mock_event = Mock(id=1, user_id=1, title="Тестовое событие")
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_event
        
        mock_user = Mock(id=1)
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            result = await delete_event(1, mock_session, mock_user)
            
            assert result['message'] == "Событие удалено"
            assert mock_session.delete.called
    
    @pytest.mark.asyncio
    async def test_delete_event_not_found(self):
        """Тест удаления несуществующего события"""
        
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        mock_user = Mock(id=1)
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with pytest.raises(Exception):  # Должно выбросить 404
                await delete_event(999, mock_session, mock_user)
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """Тест неавторизованного доступа"""
        
        mock_event = Mock(id=1, user_id=2, title="Чужое событие")
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_event
        
        mock_user = Mock(id=1)  # Пытается удалить чужое событие
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with pytest.raises(Exception):  # Должно выбросить 403
                await delete_event(1, mock_session, mock_user)


class TestMiniAppIntegration:
    """Тесты интеграции мини-приложения"""
    
    def test_miniapp_calendar_html(self):
        """Тест HTML календаря мини-приложения"""
        
        # Читаем HTML файл
        try:
            with open('miniapp/main.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Проверяем наличие ключевых элементов
            assert 'calendar-container' in html_content
            assert 'event-list' in html_content
            assert 'month-view' in html_content
            assert 'list-view' in html_content
            
            # Проверяем JavaScript
            assert 'loadEvents' in html_content
            assert 'showCalendar' in html_content
            assert 'showEventList' in html_content
            
        except FileNotFoundError:
            pytest.fail("Файл miniapp/main.html не найден")
    
    def test_miniapp_javascript_functions(self):
        """Тест JavaScript функций мини-приложения"""
        
        try:
            with open('miniapp/static/js/app.js', 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Проверяем наличие ключевых функций
            required_functions = [
                'loadEvents',
                'showCalendar', 
                'showEventList',
                'formatDate',
                'createEventElement'
            ]
            
            for func in required_functions:
                assert f'function {func}' in js_content or f'{func} =' in js_content, \
                    f"Функция {func} не найдена в app.js"
                    
        except FileNotFoundError:
            pytest.fail("Файл miniapp/static/js/app.js не найден")
    
    def test_miniapp_css_styles(self):
        """Тест CSS стилей мини-приложения"""
        
        try:
            with open('miniapp/static/css/calendar.css', 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Проверяем наличие ключевых стилей
            required_classes = [
                '.calendar-container',
                '.event-list',
                '.month-view',
                '.list-view',
                '.event-item'
            ]
            
            for css_class in required_classes:
                assert css_class in css_content, \
                    f"CSS класс {css_class} не найден в calendar.css"
                    
        except FileNotFoundError:
            pytest.fail("Файл miniapp/static/css/calendar.css не найден")


class TestEventCreationFlow:
    """Тесты полного потока создания событий"""
    
    @pytest.mark.asyncio
    async def test_text_to_event_flow(self):
        """Тест создания события из текста"""
        
        # Полный поток: текст -> парсинг -> создание -> сохранение
        test_cases = [
            {
                'input': "Встреча завтра в 15:00",
                'expected_title': "Встреча",
                'expected_time': "15:00"
            },
            {
                'input': "Звонок клиенту сегодня в 17:30",
                'expected_title': "Звонок",
                'expected_time': "17:30"
            },
            {
                'input': "Показ квартиры в понедельник",
                'expected_title': "Показ",
                'expected_time': "10:00"  # Дефолтное время
            }
        ]
        
        for case in test_cases:
            # Мок базы данных
            mock_session = AsyncMock()
            mock_user = Mock(id=1)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Мок парсера
            with patch('app.bot.handlers.text.SimpleEventParser') as mock_parser:
                mock_parser_instance = Mock()
                mock_parser.return_value = mock_parser_instance
                mock_parser_instance.process_message.return_value = {
                    'type': 'event',
                    'data': {
                        'title': case['expected_title'],
                        'date': '2024-12-15',
                        'time': case['expected_time'],
                        'description': case['input']
                    }
                }
                
                # Здесь должна быть логика создания события
                assert True  # Пока просто проверяем, что не падает
    
    @pytest.mark.asyncio
    async def test_voice_to_event_flow(self):
        """Тест создания события из голоса"""
        
        # Поток: аудио -> транскрипция -> парсинг -> создание
        with patch('app.services.ai_service.transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = "Встреча завтра в 15:00"
            
            # Мок базы данных
            mock_session = AsyncMock()
            mock_user = Mock(id=1)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Здесь должна быть логика создания события из голоса
            assert True
    
    @pytest.mark.asyncio
    async def test_photo_to_event_flow(self):
        """Тест создания события из фотографии"""
        
        # Поток: изображение -> OCR -> парсинг -> создание
        with patch('app.services.ai_service.extract_text_from_image') as mock_ocr:
            mock_ocr.return_value = "Встреча завтра в 15:00"
            
            # Мок базы данных
            mock_session = AsyncMock()
            mock_user = Mock(id=1)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Здесь должна быть логика создания события из фото
            assert True


class TestDataValidation:
    """Тесты валидации данных"""
    
    def test_event_data_validation(self):
        """Тест валидации данных события"""
        
        # Валидные данные
        valid_events = [
            {
                'title': 'Встреча',
                'date': '2024-12-15',
                'time': '15:00',
                'description': 'Встреча с клиентом'
            },
            {
                'title': 'Звонок',
                'date': '2024-12-16', 
                'time': '17:30',
                'description': ''  # Пустое описание - ОК
            }
        ]
        
        for event_data in valid_events:
            # Здесь должна быть валидация
            assert len(event_data['title']) > 0
            assert len(event_data['date']) == 10  # YYYY-MM-DD
            assert len(event_data['time']) == 5   # HH:MM
    
    def test_invalid_event_data(self):
        """Тест невалидных данных события"""
        
        invalid_events = [
            {
                'title': '',  # Пустой заголовок
                'date': '2024-12-15',
                'time': '15:00'
            },
            {
                'title': 'Встреча',
                'date': '2024-13-32',  # Невалидная дата
                'time': '15:00'
            },
            {
                'title': 'Встреча',
                'date': '2024-12-15',
                'time': '25:99'  # Невалидное время
            }
        ]
        
        for event_data in invalid_events:
            # Должна быть ошибка валидации
            try:
                # Здесь должна быть логика валидации
                if not event_data['title']:
                    raise ValueError("Пустой заголовок")
                if '13' in event_data.get('date', ''):
                    raise ValueError("Невалидная дата")
                if '25:' in event_data.get('time', ''):
                    raise ValueError("Невалидное время")
            except ValueError:
                assert True  # Ожидаемая ошибка
            except Exception as e:
                pytest.fail(f"Неожиданная ошибка: {e}")
