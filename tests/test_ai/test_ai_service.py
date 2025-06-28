"""
Тесты для AI сервиса
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.ai.ai_service import AIService
from app.ai.nlp.real_estate_parser import PropertyInfo


class TestAIService:
    """Тесты для AIService"""
    
    @pytest.fixture
    def ai_service(self):
        """Создает экземпляр AIService для тестирования"""
        with patch('app.ai.ai_service.WhisperClient'), \
             patch('app.ai.ai_service.GPTClient'), \
             patch('app.ai.ai_service.OCRClient'), \
             patch('app.ai.ai_service.RealEstateParser'):
            
            service = AIService("test-openai-key")
            return service
    
    @pytest.mark.asyncio
    async def test_process_text_message(self, ai_service):
        """Тест обработки текстового сообщения"""
        # Подготавливаем мок данные
        test_text = "Продается квартира 2 комнаты 50 кв.м за 5 млн рублей"
        
        # Мокаем парсер
        mock_property_info = PropertyInfo(
            property_type="квартира",
            rooms=2,
            area=50.0,
            price=5000000,
            confidence=0.8
        )
        ai_service.real_estate_parser.parse_text.return_value = mock_property_info
        ai_service.real_estate_parser.validate_property_info.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Мокаем GPT
        ai_service.gpt_client.extract_real_estate_info = AsyncMock(return_value={
            "property_type": "квартира",
            "rooms": 2,
            "area": 50,
            "price": 5000000
        })
        
        # Выполняем тест
        result = await ai_service.process_text_message(test_text)
        
        # Проверяем результат
        assert "error" not in result
        assert result["original_text"] == test_text
        assert result["property_info"] == mock_property_info
        assert result["validation_result"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_process_text_message_error(self, ai_service):
        """Тест обработки ошибки в текстовом сообщении"""
        # Мокаем ошибку
        ai_service.real_estate_parser.parse_text.side_effect = Exception("Test error")
        
        # Выполняем тест
        result = await ai_service.process_text_message("test text")
        
        # Проверяем результат
        assert "error" in result
        assert "Test error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_voice_message(self, ai_service):
        """Тест обработки голосового сообщения"""
        # Подготавливаем мок данные
        test_audio_path = "/tmp/test_audio.wav"
        transcribed_text = "Продается квартира 2 комнаты 50 кв.m за 5 млн рублей"
        
        # Мокаем Whisper
        ai_service.whisper_client.is_audio_valid = AsyncMock(return_value=True)
        ai_service.whisper_client.transcribe_audio = AsyncMock(return_value=transcribed_text)
        
        # Мокаем парсер
        mock_property_info = PropertyInfo(
            property_type="квартира",
            rooms=2,
            area=50.0,
            price=5000000,
            confidence=0.7
        )
        ai_service.real_estate_parser.parse_text.return_value = mock_property_info
        
        # Мокаем GPT
        ai_service.gpt_client.extract_real_estate_info = AsyncMock(return_value={
            "property_type": "квартира",
            "rooms": 2,
            "area": 50,
            "price": 5000000
        })
        
        # Выполняем тест
        result = await ai_service.process_voice_message(test_audio_path)
        
        # Проверяем результат
        assert "error" not in result
        assert result["transcribed_text"] == transcribed_text
        assert result["property_info"] == mock_property_info
        assert result["audio_file"] == test_audio_path
    
    @pytest.mark.asyncio
    async def test_process_voice_message_invalid_audio(self, ai_service):
        """Тест обработки невалидного аудио файла"""
        # Мокаем невалидный аудио файл
        ai_service.whisper_client.is_audio_valid = AsyncMock(return_value=False)
        
        # Выполняем тест
        result = await ai_service.process_voice_message("/tmp/invalid.wav")
        
        # Проверяем результат
        assert "error" in result
        assert "Invalid audio file" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_image(self, ai_service):
        """Тест обработки изображения"""
        # Подготавливаем мок данные
        test_image_path = "/tmp/test_image.jpg"
        extracted_text = "Продается квартира 2 комнаты 50 кв.m за 5 млн рублей"
        
        # Мокаем OCR
        ai_service.ocr_client.is_image_valid = AsyncMock(return_value=True)
        ai_service.ocr_client.extract_text_from_image = AsyncMock(return_value={
            "text": extracted_text,
            "confidence": 0.9,
            "text_blocks": [],
            "total_blocks": 0
        })
        
        # Мокаем парсер
        mock_property_info = PropertyInfo(
            property_type="квартира",
            rooms=2,
            area=50.0,
            price=5000000,
            confidence=0.8
        )
        ai_service.real_estate_parser.parse_text.return_value = mock_property_info
        ai_service.real_estate_parser.validate_property_info.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Мокаем GPT
        ai_service.gpt_client.extract_real_estate_info = AsyncMock(return_value={
            "property_type": "квартира",
            "rooms": 2,
            "area": 50,
            "price": 5000000
        })
        
        # Выполняем тест
        result = await ai_service.process_image(test_image_path)
        
        # Проверяем результат
        assert "error" not in result
        assert result["extracted_text"] == extracted_text
        assert result["property_info"] == mock_property_info
        assert result["image_file"] == test_image_path
    
    @pytest.mark.asyncio
    async def test_answer_question(self, ai_service):
        """Тест ответа на вопрос"""
        # Подготавливаем мок данные
        test_question = "Как правильно оформить договор купли-продажи?"
        expected_answer = "Для оформления договора купли-продажи необходимо..."
        
        # Мокаем GPT
        ai_service.gpt_client.answer_question = AsyncMock(return_value=expected_answer)
        
        # Выполняем тест
        result = await ai_service.answer_question(test_question)
        
        # Проверяем результат
        assert result == expected_answer
    
    @pytest.mark.asyncio
    async def test_answer_question_no_gpt(self, ai_service):
        """Тест ответа на вопрос без GPT"""
        # Отключаем GPT
        ai_service.gpt_client = None
        
        # Выполняем тест
        result = await ai_service.answer_question("test question")
        
        # Проверяем результат
        assert "недоступна" in result
    
    @pytest.mark.asyncio
    async def test_suggest_meeting_time(self, ai_service):
        """Тест предложения времени встречи"""
        # Подготавливаем мок данные
        client_prefs = "Хочу встретиться в будни после 18:00"
        agent_schedule = "Свободен в будни с 18:00 до 20:00"
        expected_suggestion = "Предлагаю встретиться в среду в 18:30"
        
        # Мокаем GPT
        ai_service.gpt_client.suggest_meeting_time = AsyncMock(return_value=expected_suggestion)
        
        # Выполняем тест
        result = await ai_service.suggest_meeting_time(client_prefs, agent_schedule)
        
        # Проверяем результат
        assert result == expected_suggestion
    
    def test_get_service_status(self, ai_service):
        """Тест получения статуса сервиса"""
        # Выполняем тест
        status = ai_service.get_service_status()
        
        # Проверяем структуру статуса
        assert "whisper_client" in status
        assert "gpt_client" in status
        assert "ocr_client" in status
        assert "real_estate_parser" in status
        assert "overall" in status
        
        # Проверяем общий статус
        assert "available_components" in status["overall"]
        assert "total_components" in status["overall"]
        assert "fully_operational" in status["overall"]
    
    @pytest.mark.asyncio
    async def test_process_mixed_content(self, ai_service):
        """Тест обработки смешанного контента"""
        # Подготавливаем мок данные
        test_text = "Продается квартира"
        test_audio_path = "/tmp/test_audio.wav"
        test_image_path = "/tmp/test_image.jpg"
        
        # Мокаем обработчики
        ai_service.process_text_message = AsyncMock(return_value={
            "property_info": PropertyInfo(property_type="квартира", confidence=0.8)
        })
        ai_service.process_voice_message = AsyncMock(return_value={
            "property_info": PropertyInfo(price=5000000, confidence=0.7)
        })
        ai_service.process_image = AsyncMock(return_value={
            "property_info": PropertyInfo(area=50.0, confidence=0.9)
        })
        
        # Выполняем тест
        result = await ai_service.process_mixed_content(
            text=test_text,
            audio_file_path=test_audio_path,
            image_file_path=test_image_path
        )
        
        # Проверяем результат
        assert "error" not in result
        assert result["text_processing"] is not None
        assert result["voice_processing"] is not None
        assert result["image_processing"] is not None
        assert result["combined_property_info"] is not None
        
        # Проверяем объединенную информацию
        combined_info = result["combined_property_info"]
        assert combined_info.property_type == "квартира"
        assert combined_info.price == 5000000
        assert combined_info.area == 50.0 