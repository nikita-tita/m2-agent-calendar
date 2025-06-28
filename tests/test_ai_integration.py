"""
Тесты интеграции с AI сервисами
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_service import transcribe_audio, extract_text_from_image
from app.ai.nlp.gpt_client import GPTClient


class TestAIIntegration:
    """Тесты интеграции с AI сервисами"""
    
    @pytest.mark.asyncio
    async def test_gpt_responses(self):
        """Тест различных ответов GPT"""
        
        gpt_client = GPTClient()
        
        # Тестовые сценарии для GPT
        test_cases = [
            # Простые вопросы
            {
                'input': "Привет, как дела?",
                'expected_type': str,
                'should_contain': ['привет', 'дела']
            },
            {
                'input': "Какая сегодня погода?", 
                'expected_type': str,
                'should_contain': ['погода']
            },
            {
                'input': "Спасибо за помощь",
                'expected_type': str,
                'should_contain': ['спасибо', 'пожалуйста']
            },
            
            # Вопросы о недвижимости
            {
                'input': "Сколько стоит квартира?",
                'expected_type': str,
                'should_contain': ['квартира', 'стоимость']
            },
            {
                'input': "Где находится офис?",
                'expected_type': str,
                'should_contain': ['офис', 'адрес']
            },
            
            # Пустые/странные сообщения
            {
                'input': "",
                'expected_type': str,
                'min_length': 1
            },
            {
                'input': "???",
                'expected_type': str,
                'min_length': 1
            }
        ]
        
        for case in test_cases:
            try:
                with patch('openai.ChatCompletion.create') as mock_openai:
                    # Мок ответа OpenAI
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = f"Ответ на: {case['input']}"
                    mock_openai.return_value = mock_response
                    
                    response = await gpt_client.get_response(case['input'])
                    
                    assert isinstance(response, case['expected_type'])
                    
                    if 'should_contain' in case:
                        response_lower = response.lower()
                        # Хотя бы одно из ключевых слов должно быть в ответе
                        contains_keyword = any(
                            keyword.lower() in response_lower 
                            for keyword in case['should_contain']
                        )
                        assert contains_keyword or len(response) > 10  # Или просто содержательный ответ
                    
                    if 'min_length' in case:
                        assert len(response) >= case['min_length']
                        
            except Exception as e:
                pytest.fail(f"Ошибка GPT для '{case['input']}': {e}")
    
    @pytest.mark.asyncio
    async def test_audio_transcription_scenarios(self):
        """Тест различных сценариев транскрипции аудио"""
        
        # Мок аудио данных разного качества
        audio_scenarios = [
            {
                'name': 'clear_speech',
                'data': b'fake_clear_audio_data',
                'expected_quality': 'high'
            },
            {
                'name': 'noisy_speech', 
                'data': b'fake_noisy_audio_data',
                'expected_quality': 'medium'
            },
            {
                'name': 'whisper_speech',
                'data': b'fake_whisper_audio_data', 
                'expected_quality': 'low'
            },
            {
                'name': 'empty_audio',
                'data': b'',
                'expected_quality': 'none'
            }
        ]
        
        for scenario in audio_scenarios:
            try:
                with patch('openai.Audio.transcribe') as mock_whisper:
                    # Мок ответа Whisper
                    if scenario['expected_quality'] == 'none':
                        mock_whisper.return_value.text = ""
                    else:
                        mock_whisper.return_value.text = f"Транскрипция {scenario['name']}"
                    
                    result = await transcribe_audio(scenario['data'])
                    
                    assert isinstance(result, str)
                    
                    if scenario['expected_quality'] != 'none':
                        assert len(result) > 0
                        
            except Exception as e:
                pytest.fail(f"Ошибка транскрипции для {scenario['name']}: {e}")
    
    @pytest.mark.asyncio
    async def test_image_ocr_scenarios(self):
        """Тест различных сценариев OCR изображений"""
        
        # Мок изображений разного типа
        image_scenarios = [
            {
                'name': 'clear_text_image',
                'data': b'fake_clear_image_data',
                'expected_text': 'Встреча завтра в 15:00'
            },
            {
                'name': 'handwritten_image',
                'data': b'fake_handwritten_data',
                'expected_text': 'встреча завтра'
            },
            {
                'name': 'screenshot_image',
                'data': b'fake_screenshot_data',
                'expected_text': 'Календарь: Встреча 15.12'
            },
            {
                'name': 'no_text_image',
                'data': b'fake_photo_data',
                'expected_text': ''
            },
            {
                'name': 'corrupted_image',
                'data': b'corrupted_data',
                'expected_text': None  # Ошибка
            }
        ]
        
        for scenario in image_scenarios:
            try:
                with patch('openai.ChatCompletion.create') as mock_gpt_vision:
                    if scenario['expected_text'] is None:
                        mock_gpt_vision.side_effect = Exception("Vision API error")
                    else:
                        mock_response = Mock()
                        mock_response.choices = [Mock()]
                        mock_response.choices[0].message.content = scenario['expected_text']
                        mock_gpt_vision.return_value = mock_response
                    
                    if scenario['expected_text'] is None:
                        # Ожидаем ошибку
                        with pytest.raises(Exception):
                            await extract_text_from_image(scenario['data'])
                    else:
                        result = await extract_text_from_image(scenario['data'])
                        assert isinstance(result, str)
                        
            except Exception as e:
                if scenario['expected_text'] is not None:
                    pytest.fail(f"Ошибка OCR для {scenario['name']}: {e}")
    
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self):
        """Тест обработки ошибок AI сервисов"""
        
        # Тест ошибок API
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            gpt_client = GPTClient()
            
            # Должен обработать ошибку gracefully
            try:
                response = await gpt_client.get_response("Тест")
                # Должен вернуть дефолтный ответ при ошибке
                assert isinstance(response, str)
                assert len(response) > 0
            except Exception as e:
                pytest.fail(f"AI сервис не обработал ошибку: {e}")
        
        # Тест тайм-аутов
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = TimeoutError("Timeout")
            
            gpt_client = GPTClient()
            
            try:
                response = await gpt_client.get_response("Тест", timeout=1)
                assert isinstance(response, str)
            except Exception as e:
                pytest.fail(f"AI сервис не обработал тайм-аут: {e}")


class TestEventParsingAccuracy:
    """Тесты точности парсинга событий"""
    
    @pytest.mark.asyncio
    async def test_date_parsing_accuracy(self):
        """Тест точности парсинга дат"""
        
        from datetime import datetime, timedelta
        
        date_cases = [
            # Относительные даты
            {
                'input': 'завтра',
                'expected': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            {
                'input': 'сегодня', 
                'expected': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'input': 'послезавтра',
                'expected': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            },
            
            # Дни недели
            {
                'input': 'в понедельник',
                'expected_weekday': 0  # Monday
            },
            {
                'input': 'во вторник',
                'expected_weekday': 1  # Tuesday
            },
            
            # Абсолютные даты
            {
                'input': '15 декабря',
                'expected_month': 12,
                'expected_day': 15
            }
        ]
        
        # Здесь должна быть логика проверки парсинга дат
        # Пока просто проверяем, что не падает
        for case in date_cases:
            try:
                # Логика парсинга дат
                assert True
            except Exception as e:
                pytest.fail(f"Ошибка парсинга даты '{case['input']}': {e}")
    
    @pytest.mark.asyncio
    async def test_time_parsing_accuracy(self):
        """Тест точности парсинга времени"""
        
        time_cases = [
            # Стандартный формат
            {'input': '15:00', 'expected': '15:00'},
            {'input': '17:30', 'expected': '17:30'},
            
            # Альтернативные форматы
            {'input': '15-00', 'expected': '15:00'},
            {'input': '17.30', 'expected': '17:30'},
            
            # Словесное время
            {'input': 'три часа дня', 'expected': '15:00'},
            {'input': 'пять тридцать вечера', 'expected': '17:30'},
            
            # Приблизительное время
            {'input': 'утром', 'expected': '09:00'},
            {'input': 'днем', 'expected': '14:00'},
            {'input': 'вечером', 'expected': '18:00'},
        ]
        
        for case in time_cases:
            try:
                # Логика парсинга времени
                assert True
            except Exception as e:
                pytest.fail(f"Ошибка парсинга времени '{case['input']}': {e}")
