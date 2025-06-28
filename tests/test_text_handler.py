"""
Комплексные тесты текстового обработчика
Все возможные кейсы пользовательского ввода
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.handlers.text import handle_text_message


class TestTextHandlerCases:
    """Тесты различных кейсов текстовых сообщений"""
    
    @pytest.mark.asyncio
    async def test_event_creation_cases(self):
        """Тест создания событий из разных форматов"""
        
        # Мок объектов
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_message.text = "Встреча завтра в 15:00"
        
        mock_bot = AsyncMock()
        mock_session = AsyncMock()
        
        # Мок пользователя
        mock_user = Mock()
        mock_user.id = 1
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Тестовые случаи создания событий
        test_cases = [
            # Базовые форматы
            "Встреча завтра в 15:00",
            "Звонок сегодня в 17:30",
            "Показ в понедельник в 14:00",
            
            # С описанием
            "Встреча с клиентом Ивановым завтра в 15:00",
            "Звонок по поводу квартиры сегодня в 17:30",
            "Показ двухкомнатной квартиры в понедельник",
            
            # Императивные команды
            "Запланируй встречу на завтра в 15:00",
            "Поставь звонок на сегодня в 17:30",
            "Добавь показ на понедельник в 14:00",
            
            # Разговорная речь
            "У меня встреча завтра в три часа дня",
            "Нужно позвонить клиенту сегодня вечером",
            "Показываю квартиру в понедельник утром",
            
            # Неформальные варианты
            "встреча завтра 15-00",
            "звонок сегодня 17.30",
            "показ понедельник 2 часа",
        ]
        
        for case in test_cases:
            mock_message.text = case
            try:
                await handle_text_message(mock_message, mock_bot, mock_session)
                # Проверяем, что бот отправил ответ
                assert mock_bot.send_message.called
                mock_bot.send_message.reset_mock()
            except Exception as e:
                pytest.fail(f"Ошибка обработки '{case}': {e}")
    
    @pytest.mark.asyncio
    async def test_non_event_messages(self):
        """Тест сообщений, которые НЕ являются событиями"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_bot = AsyncMock()
        mock_session = AsyncMock()
        
        non_event_cases = [
            # Приветствия
            "Привет!",
            "Здравствуйте",
            "Добрый день",
            
            # Вопросы
            "Как дела?",
            "Что нового?",
            "Какая погода?",
            "Сколько стоит квартира?",
            "Где находится офис?",
            
            # Благодарности
            "Спасибо",
            "Благодарю за помощь",
            "Отлично, спасибо!",
            
            # Общие фразы
            "Понятно",
            "Хорошо",
            "Ладно",
            "Окей",
        ]
        
        for case in non_event_cases:
            mock_message.text = case
            try:
                await handle_text_message(mock_message, mock_bot, mock_session)
                # Должен отправить GPT ответ
                assert mock_bot.send_message.called
                mock_bot.send_message.reset_mock()
            except Exception as e:
                pytest.fail(f"Ошибка обработки '{case}': {e}")
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Тест граничных и проблемных случаев"""
        
        mock_message = Mock()
        mock_message.from_user.id = 123456789
        mock_bot = AsyncMock()
        mock_session = AsyncMock()
        
        edge_cases = [
            # Пустые и странные сообщения
            "",
            "   ",
            "\n\n\n",
            ".",
            "???",
            "!!!",
            
            # Только время без события
            "15:00",
            "в 3 часа",
            "17-30",
            
            # Только дата без события
            "завтра",
            "в понедельник",
            "сегодня",
            
            # Некорректное время
            "встреча в 25:99",
            "звонок в 30:00",
            
            # Некорректная дата
            "встреча 32 февраля",
            "звонок в пятницу 13-го",
            
            # Очень длинные сообщения
            "Встреча " + "очень " * 50 + "важная завтра в 15:00",
            
            # Специальные символы
            "Встреча @#$%^&*() завтра в 15:00",
            "Звонок 📞 сегодня в 17:30",
            "Показ 🏠 в понедельник",
            
            # Смешанные языки
            "Meeting завтра в 15:00",
            "Встреча tomorrow at 3pm",
        ]
        
        for case in edge_cases:
            mock_message.text = case
            try:
                await handle_text_message(mock_message, mock_bot, mock_session)
                # Должен обработать без ошибок
                assert True
            except Exception as e:
                pytest.fail(f"Падение на граничном случае '{case}': {e}")
