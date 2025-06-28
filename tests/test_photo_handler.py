"""
Тесты обработчика фотографий
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.handlers.photo import handle_photo_message


class TestPhotoHandlerCases:
    """Тесты различных кейсов обработки фотографий"""
    
    @pytest.mark.asyncio
    async def test_photo_ocr_success(self):
        """Тест успешного OCR фотографии"""
        
        # Мок объектов
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.photo = [Mock(file_id="photo_123")]
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "photos/photo.jpg"
        mock_bot.download_file.return_value = b"fake_image_data"
        
        mock_session = AsyncMock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Мок AI сервиса
        with patch('app.services.ai_service.extract_text_from_image') as mock_ocr:
            mock_ocr.return_value = "Встреча завтра в 15:00"
            
            await handle_photo_message(mock_message, mock_bot, mock_session)
            
            # Проверяем, что OCR был вызван
            assert mock_ocr.called
            # Проверяем, что бот отправил ответ
            assert mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_photo_ocr_scenarios(self):
        """Тест различных сценариев OCR"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.photo = [Mock(file_id="photo_123")]
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "photos/photo.jpg"
        mock_bot.download_file.return_value = b"fake_image_data"
        
        mock_session = AsyncMock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Различные сценарии OCR
        ocr_cases = [
            # Четкий текст с событиями
            "Встреча с клиентом 15.12.2024 в 15:00",
            "Звонок Иванову завтра 17:30",
            "Показ квартиры понедельник 14:00",
            
            # Рукописный текст
            "встреча завтра 3 часа",
            "звонок сегодня вечер",
            
            # Смешанный текст
            "ВСТРЕЧА: завтра в 15:00\nАдрес: ул. Ленина 1",
            "Звонок клиенту\nВремя: сегодня 17:30",
            
            # Документы/скриншоты
            "Календарь\n15 декабря - Встреча\n16 декабря - Звонок",
            "TODO:\n- Встреча завтра\n- Звонок сегодня",
            
            # Нечеткий/искаженный текст
            "Встр3ча з@втра в 15:00",
            "3в0н0к сег0дня",
            
            # Пустой результат OCR
            "",
            "   ",
            "Текст не распознан",
            
            # Не связанный с событиями текст
            "Привет, как дела?",
            "Красивая фотография",
            "Спасибо за помощь",
        ]
        
        for ocr_text in ocr_cases:
            with patch('app.services.ai_service.extract_text_from_image') as mock_ocr:
                mock_ocr.return_value = ocr_text
                
                try:
                    await handle_photo_message(mock_message, mock_bot, mock_session)
                    assert mock_bot.send_message.called
                    mock_bot.send_message.reset_mock()
                except Exception as e:
                    pytest.fail(f"Ошибка обработки OCR '{ocr_text}': {e}")
    
    @pytest.mark.asyncio
    async def test_photo_download_error(self):
        """Тест ошибки скачивания фотографии"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.photo = [Mock(file_id="photo_123")]
        
        mock_bot = AsyncMock()
        mock_bot.get_file.side_effect = Exception("Download error")
        
        mock_session = AsyncMock()
        
        await handle_photo_message(mock_message, mock_bot, mock_session)
        
        # Должен отправить сообщение об ошибке
        assert mock_bot.send_message.called
        call_args = mock_bot.send_message.call_args
        assert "Не удалось обработать изображение" in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_ocr_error(self):
        """Тест ошибки OCR"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.photo = [Mock(file_id="photo_123")]
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "photos/photo.jpg"
        mock_bot.download_file.return_value = b"fake_image_data"
        
        mock_session = AsyncMock()
        
        with patch('app.services.ai_service.extract_text_from_image') as mock_ocr:
            mock_ocr.side_effect = Exception("OCR error")
            
            await handle_photo_message(mock_message, mock_bot, mock_session)
            
            # Должен отправить сообщение об ошибке
            assert mock_bot.send_message.called
            call_args = mock_bot.send_message.call_args
            assert "Не удалось обработать изображение" in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_empty_photo_array(self):
        """Тест пустого массива фотографий"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.photo = []
        
        mock_bot = AsyncMock()
        mock_session = AsyncMock()
        
        await handle_photo_message(mock_message, mock_bot, mock_session)
        
        # Должен отправить сообщение об ошибке
        assert mock_bot.send_message.called
        call_args = mock_bot.send_message.call_args
        assert "Не удалось обработать изображение" in call_args[1]['text']
