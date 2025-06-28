"""
Тесты голосового обработчика
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.handlers.voice import handle_voice_message


class TestVoiceHandlerCases:
    """Тесты различных кейсов голосовых сообщений"""
    
    @pytest.mark.asyncio
    async def test_voice_transcription_success(self):
        """Тест успешной транскрипции голоса"""
        
        # Мок объектов
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.voice.file_id = "voice_file_123"
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "voice/file.ogg"
        mock_bot.download_file.return_value = b"fake_audio_data"
        
        mock_session = AsyncMock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Мок AI сервиса
        with patch('app.services.ai_service.transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = "Встреча завтра в 15:00"
            
            await handle_voice_message(mock_message, mock_bot, mock_session)
            
            # Проверяем, что транскрипция была вызвана
            assert mock_transcribe.called
            # Проверяем, что бот отправил ответ
            assert mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_voice_transcription_scenarios(self):
        """Тест различных сценариев транскрипции"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.voice.file_id = "voice_file_123"
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "voice/file.ogg"
        mock_bot.download_file.return_value = b"fake_audio_data"
        
        mock_session = AsyncMock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Различные сценарии транскрипции
        transcription_cases = [
            # События
            "Встреча завтра в 15:00",
            "Звонок клиенту сегодня в 17:30",
            "Показ квартиры в понедельник",
            
            # Команды
            "Удали последнее событие",
            "Покажи мой календарь",
            "Перенеси встречу",
            
            # Обычные сообщения
            "Привет, как дела?",
            "Спасибо за помощь",
            "Какая сегодня погода?",
            
            # Нечеткая речь
            "эээ... встреча... завтра... в три часа",
            "ну... звонок... сегодня вечером",
            
            # Пустая транскрипция
            "",
            "   ",
        ]
        
        for transcription in transcription_cases:
            with patch('app.services.ai_service.transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = transcription
                
                try:
                    await handle_voice_message(mock_message, mock_bot, mock_session)
                    assert mock_bot.send_message.called
                    mock_bot.send_message.reset_mock()
                except Exception as e:
                    pytest.fail(f"Ошибка обработки транскрипции '{transcription}': {e}")
    
    @pytest.mark.asyncio
    async def test_voice_download_error(self):
        """Тест ошибки скачивания голосового файла"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.voice.file_id = "voice_file_123"
        
        mock_bot = AsyncMock()
        mock_bot.get_file.side_effect = Exception("Download error")
        
        mock_session = AsyncMock()
        
        await handle_voice_message(mock_message, mock_bot, mock_session)
        
        # Должен отправить сообщение об ошибке
        assert mock_bot.send_message.called
        call_args = mock_bot.send_message.call_args
        assert "Не удалось обработать голосовое сообщение" in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_transcription_error(self):
        """Тест ошибки транскрипции"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.voice.file_id = "voice_file_123"
        
        mock_bot = AsyncMock()
        mock_bot.get_file.return_value.file_path = "voice/file.ogg"
        mock_bot.download_file.return_value = b"fake_audio_data"
        
        mock_session = AsyncMock()
        
        with patch('app.services.ai_service.transcribe_audio') as mock_transcribe:
            mock_transcribe.side_effect = Exception("Transcription error")
            
            await handle_voice_message(mock_message, mock_bot, mock_session)
            
            # Должен отправить сообщение об ошибке
            assert mock_bot.send_message.called
            call_args = mock_bot.send_message.call_args
            assert "Не удалось обработать голосовое сообщение" in call_args[1]['text']
