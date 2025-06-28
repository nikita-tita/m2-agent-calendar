"""
Упрощённый обработчик текстовых сообщений
Только события + GPT ответы
"""
import logging
from datetime import datetime, timedelta, time
from typing import Dict, Any, Optional, List
import re

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.event import Event
from app.ai.nlp.gpt_client import GPTClient
from app.config import settings
from app.bot.keyboards.inline import get_event_actions_keyboard

logger = logging.getLogger(__name__)
router = Router()

class SimpleEventParser:
    """Простой парсер событий с GPT"""
    
    def __init__(self):
        self.gpt_client = None
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
                self.gpt_client = GPTClient(settings.OPENAI_API_KEY)
                logger.info("GPT client initialized")
        except Exception as e:
            logger.warning(f"GPT client not available: {e}")
    
    async def process_message(self, text: str) -> Dict[str, Any]:
        """Обрабатывает сообщение - либо создаёт событие, либо даёт ответ"""
        
        # Сначала пробуем парсить как событие
        event_data = await self._try_parse_event(text)
        if event_data:
            return {
                'type': 'event',
                'data': event_data
            }
        
        # Если не событие - проверяем команды управления
        command_result = await self._try_parse_command(text)
        if command_result:
            return command_result
        
        # Иначе - GPT ответ
        gpt_response = await self._get_gpt_response(text)
        return {
            'type': 'response',
            'message': gpt_response
        }
    
    async def _try_parse_event(self, text: str) -> Optional[Dict[str, Any]]:
        """Пытается распарсить событие"""
        
        # Ключевые слова событий
        event_keywords = [
            'встреча', 'звонок', 'показ', 'созвон', 'дело', 'задача',
            'напомни', 'запланируй', 'поставь', 'добавь'
        ]
        
        if not any(word in text.lower() for word in event_keywords):
            return None
        
        # Используем GPT для парсинга
        if self.gpt_client:
            try:
                result = await self.gpt_client.parse_calendar_event(text)
                confidence = result.get('confidence', 0)
                if isinstance(confidence, str):
                    confidence = float(confidence) if confidence.replace('.', '').isdigit() else 0
                
                if confidence > 0.5:
                    return result
            except Exception as e:
                logger.warning(f"GPT parsing failed: {e}")
        
        # Fallback простой парсер
        return self._simple_parse(text)
    
    def _simple_parse(self, text: str) -> Dict[str, Any]:
        """Простой fallback парсер"""
        now = datetime.now()
        
        # Определяем дату
        date_str = now.strftime("%Y-%m-%d")
        if 'завтра' in text:
            date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif 'послезавтра' in text:
            date_str = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Извлекаем время
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        time_str = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else "10:00"
        
        # Генерируем заголовок
        if 'звонок' in text.lower():
            title = "Звонок"
        elif 'встреча' in text.lower():
            title = "Встреча"
        elif 'показ' in text.lower():
            title = "Показ"
        else:
            title = "Событие"
        
        return {
            'title': title,
            'date': date_str,
            'time': time_str,
            'event_type': 'meeting',
            'confidence': 0.8
        }
    
    async def _try_parse_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Парсит команды управления событиями"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['удали', 'отмени', 'убери']):
            return {
                'type': 'command',
                'action': 'delete',
                'message': 'Какое событие удалить? Покажите список ваших событий.'
            }
        
        if any(word in text_lower for word in ['перенеси', 'измени', 'поменяй']):
            return {
                'type': 'command', 
                'action': 'modify',
                'message': 'Какое событие изменить? Покажите список ваших событий.'
            }
        
        if any(word in text_lower for word in ['список', 'события', 'календарь', 'покажи']):
            return {
                'type': 'command',
                'action': 'list',
                'message': 'Открываю ваш календарь...'
            }
        
        return None
    
    async def _get_gpt_response(self, text: str) -> str:
        """Получает ответ от GPT"""
        if not self.gpt_client:
            return "🤔 Не понял ваш запрос. Попробуйте создать событие: 'Встреча завтра в 15:00'"
        
        try:
            # Простой промпт для GPT
            prompt = f"""Ты помощник риэлтора. Пользователь написал: "{text}"

Если это не событие для календаря, дай краткий полезный ответ (максимум 2-3 предложения).
Если это вопрос о недвижимости - дай тематический совет.
Если это общий вопрос - дай дружелюбный ответ.

Ответ:"""
            
            # Здесь можно добавить вызов GPT API для общих ответов
            return "🤖 Понял! Если хотите создать событие, скажите когда и что запланировать."
            
        except Exception as e:
            logger.error(f"GPT response failed: {e}")
            return "🤔 Не понял ваш запрос. Попробуйте создать событие: 'Встреча завтра в 15:00'"

class EventManager:
    """Упрощённый менеджер событий"""
    
    def __init__(self):
        self.parser = SimpleEventParser()
    
    async def process_text(self, text: str, telegram_user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """Обрабатывает текст"""
        
        # Получаем пользователя
        from sqlalchemy import select
        from app.models.user import User
        
        result = await session.execute(select(User).where(User.telegram_id == telegram_user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                'type': 'error',
                'message': 'Пользователь не найден. Напишите /start'
            }
        
        # Парсим сообщение
        parse_result = await self.parser.process_message(text)
        
        if parse_result['type'] == 'event':
            # Создаём событие
            return await self._create_event(parse_result['data'], user.id, session)
        
        elif parse_result['type'] == 'command':
            # Команда управления
            return {
                'type': 'command',
                'message': parse_result['message'],
                'action': parse_result.get('action')
            }
        
        else:
            # GPT ответ
            return {
                'type': 'response',
                'message': parse_result['message']
            }
    
    async def _create_event(self, event_data: Dict[str, Any], user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """Создаёт событие"""
        try:
            # Парсим дату и время
            event_date = datetime.strptime(event_data['date'], '%Y-%m-%d').date()
            time_parts = event_data['time'].split(':')
            start_time = datetime.combine(event_date, time(int(time_parts[0]), int(time_parts[1])))
            end_time = start_time + timedelta(hours=1)
            
            # Создаём событие
            event = Event(
                user_id=user_id,
                title=event_data['title'],
                start_time=start_time,
                end_time=end_time,
                event_type=event_data.get('event_type', 'meeting'),
                created_from='text',
                ai_confidence=event_data.get('confidence', 0.8)
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            # Формируем ответ
            message = f"✅ <b>Событие создано</b>\n\n"
            message += f"📅 <b>{event.title}</b>\n"
            message += f"📅 {event.start_time.strftime('%d.%m.%Y')}\n"
            message += f"🕒 {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n"
            message += f"🤖 Уверенность: {int(event.ai_confidence * 100)}%"
            
            return {
                'type': 'created',
                'message': message,
                'event': event,
                'keyboard': get_event_actions_keyboard(event.id, 'created')
            }
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {
                'type': 'error',
                'message': f'Ошибка создания события: {str(e)}'
            }

# Глобальный менеджер
event_manager = EventManager()

@router.message(F.text)
async def handle_text_message(message: Message):
    """Упрощённый обработчик текста"""
    try:
        async for session in get_async_session():
            # Обрабатываем текст
            result = await event_manager.process_text(message.text, message.from_user.id, session)
            
            if result['type'] == 'created':
                # Событие создано
                await message.answer(
                    result['message'],
                    reply_markup=result.get('keyboard'),
                    parse_mode="HTML"
                )
                
            elif result['type'] == 'command':
                # Команда
                if result.get('action') == 'list':
                    # Открываем календарь
                    from app.bot.keyboards.inline import get_calendar_keyboard
                    await message.answer(
                        "📅 <b>Ваш календарь</b>",
                        reply_markup=get_calendar_keyboard(),
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(result['message'], parse_mode="HTML")
                
            elif result['type'] == 'response':
                # GPT ответ
                await message.answer(result['message'], parse_mode="HTML")
                
            else:
                # Ошибка
                await message.answer(f"❌ {result['message']}", parse_mode="HTML")
            
            break
            
    except Exception as e:
        logger.error(f"Text handler error: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке сообщения",
            parse_mode="HTML"
        )

def register_handlers(dp: Router) -> None:
    """Регистрация обработчиков"""
    dp.include_router(router) 