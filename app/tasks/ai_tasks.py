import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="process_voice_message")
def process_voice_message(self, file_path: str, user_id: int, chat_id: int):
    """
    Асинхронно обрабатывает голосовое сообщение
    Транскрибирует в текст и создаёт событие
    """
    async def _process():
        try:
            from app.ai.speech.whisper_client import WhisperClient
            from app.bot.handlers.text import EventManager
            from app.database import get_async_session
            from aiogram import Bot
            from app.config import settings
            
            # Транскрибируем аудио
            whisper = WhisperClient()
            transcription = await whisper.transcribe_file(file_path)
            
            if not transcription or not transcription.get('text'):
                raise ValueError("Failed to transcribe audio")
            
            text = transcription['text']
            confidence = transcription.get('confidence', 0.8)
            
            # Создаём событие из текста
            event_manager = EventManager()
            async for session in get_async_session():
                result = await event_manager.process_text(text, user_id, session)
                break
            
            # Отправляем результат пользователю
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            
            message = f"🎤 <b>Голосовое сообщение обработано</b>\n\n"
            message += f"📝 <b>Распознанный текст:</b>\n{text}\n\n"
            message += f"📊 <b>Уверенность:</b> {int(confidence * 100)}%\n\n"
            
            if result['type'] == 'created':
                message += result['message']
            else:
                message += f"❌ {result.get('message', 'Не удалось создать событие')}"
            
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            await bot.session.close()
            
            # Удаляем временный файл
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {file_path}: {e}")
            
            logger.info(f"Voice message processed for user {user_id}")
            return {"status": "success", "text": text, "event_created": result['type'] == 'created'}
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            
            # Уведомляем пользователя об ошибке
            try:
                from aiogram import Bot
                from app.config import settings
                
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=chat_id,
                    text="❌ Не удалось обработать голосовое сообщение. Попробуйте ещё раз."
                )
                await bot.session.close()
            except Exception:
                pass
            
            raise self.retry(countdown=60, max_retries=2)
    
    return asyncio.run(_process())

@shared_task(bind=True, name="process_image_ocr")
def process_image_ocr(self, image_path: str, user_id: int, chat_id: int):
    """
    Асинхронно обрабатывает изображение с OCR
    Извлекает текст и создаёт событие
    """
    async def _process():
        try:
            from app.ai.vision.ocr_client import OCRClient
            from app.bot.handlers.text import EventManager
            from app.database import get_async_session
            from aiogram import Bot
            from app.config import settings
            
            # Извлекаем текст из изображения
            ocr = OCRClient()
            extracted_text = await ocr.extract_text(image_path)
            
            if not extracted_text:
                raise ValueError("No text found in image")
            
            # Обрабатываем как обычный текст
            event_manager = EventManager()
            async for session in get_async_session():
                result = await event_manager.process_text(extracted_text, user_id, session)
                break
            
            # Отправляем результат
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            
            message = f"📸 <b>Изображение обработано</b>\n\n"
            message += f"📝 <b>Распознанный текст:</b>\n{extracted_text}\n\n"
            
            if result['type'] == 'created':
                message += result['message']
            else:
                message += f"❌ {result.get('message', 'Не удалось создать событие из текста')}"
            
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            await bot.session.close()
            
            # Удаляем временный файл
            try:
                Path(image_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temp image {image_path}: {e}")
            
            logger.info(f"Image OCR processed for user {user_id}")
            return {"status": "success", "text": extracted_text, "event_created": result['type'] == 'created'}
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            
            # Уведомляем об ошибке
            try:
                from aiogram import Bot
                from app.config import settings
                
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=chat_id,
                    text="❌ Не удалось распознать текст в изображении. Попробуйте более чёткое фото."
                )
                await bot.session.close()
            except Exception:
                pass
            
            raise self.retry(countdown=60, max_retries=2)
    
    return asyncio.run(_process())

@shared_task(name="analyze_user_patterns")
def analyze_user_patterns(user_id: int):
    """
    Анализирует паттерны поведения пользователя
    Генерирует персональные рекомендации
    """
    async def _analyze():
        try:
            from app.ai.embeddings.vector_service import VectorSearchService
            from app.database import get_async_session
            from sqlalchemy import select
            from app.models.user import User
            
            vector_service = VectorSearchService()
            
            # Анализируем паттерны событий
            patterns = await vector_service.analyze_event_patterns(user_id)
            
            # Сохраняем результат анализа в БД пользователя
            async for session in get_async_session():
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if user:
                    # Обновляем метаданные пользователя
                    user.preferences = patterns
                    await session.commit()
                
                break
            
            logger.info(f"User patterns analyzed for user {user_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {}
    
    return asyncio.run(_analyze())

@shared_task(name="smart_event_suggestions")
def smart_event_suggestions(user_id: int, text: str):
    """
    Генерирует умные предложения событий на основе контекста
    """
    async def _suggest():
        try:
            from app.ai.embeddings.vector_service import VectorSearchService
            
            vector_service = VectorSearchService()
            suggestions = await vector_service.suggest_related_events(text, user_id)
            
            logger.info(f"Generated {len(suggestions)} suggestions for user {user_id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestions generation error: {e}")
            return []
    
    return asyncio.run(_suggest())

@shared_task(name="semantic_search_events")
def semantic_search_events(user_id: int, query: str, limit: int = 5):
    """
    Выполняет семантический поиск по событиям пользователя
    """
    async def _search():
        try:
            from app.ai.embeddings.vector_service import VectorSearchService
            
            vector_service = VectorSearchService()
            results = await vector_service.search_similar_events(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            logger.info(f"Semantic search returned {len(results)} results for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    return asyncio.run(_search()) 