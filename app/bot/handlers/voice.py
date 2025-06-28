"""
Упрощённый обработчик голосовых сообщений
Только распознавание речи + создание событий
"""
import logging
import tempfile
import os
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message

from app.database import get_async_session
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.voice)
async def handle_voice_message(message: Message):
    """Упрощённый обработчик голосовых сообщений"""
    
    try:
        async for session in get_async_session():
            # Начальное сообщение
            status_msg = await message.answer(
                "🎤 <b>Голосовое сообщение получено</b>\n\n"
                "🔄 Распознаю речь...",
                parse_mode="HTML"
            )
            
            # Скачиваем аудио файл
            voice = message.voice
            file_info = await message.bot.get_file(voice.file_id)
            
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                await message.bot.download_file(file_info.file_path, temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Обновляем статус
                await status_msg.edit_text(
                    "🎤 <b>Обрабатываю голос...</b>\n\n"
                    "✅ Аудио загружено\n"
                    "🔄 Распознаю речь...",
                    parse_mode="HTML"
                )

                # Инициализируем AI сервис
                ai_service = AIService()
                
                # Обрабатываем голос
                result = await ai_service.process_voice(temp_file_path)
                
                if "error" in result:
                    await status_msg.edit_text(
                        f"❌ <b>Ошибка обработки</b>\n\n"
                        f"Не удалось распознать речь: {result['error']}\n\n"
                        "💡 Попробуйте говорить более чётко",
                        parse_mode="HTML"
                    )
                    return

                # Получаем распознанный текст
                transcribed_text = result.get("transcribed_text", "")
                
                # Обновляем статус
                await status_msg.edit_text(
                    "🎤 <b>Обрабатываю голос...</b>\n\n"
                    "✅ Аудио загружено\n"
                    "✅ Речь распознана\n"
                    "🤖 Создаю событие...",
                    parse_mode="HTML"
                )

                # Формируем ответ
                response_text = "🎤 <b>Голосовое сообщение обработано</b>\n\n"
                
                if transcribed_text:
                    response_text += f"📝 <b>Распознанный текст:</b>\n<i>«{transcribed_text}»</i>\n\n"
                    
                    # 🎯 АВТОМАТИЧЕСКОЕ СОЗДАНИЕ СОБЫТИЯ ИЗ РЕЧИ
                    try:
                        from app.bot.handlers.text import EventManager
                        event_manager = EventManager()
                        
                        # Получаем пользователя из БД
                        from sqlalchemy import select
                        from app.models.user import User
                        result_user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
                        db_user = result_user.scalar_one_or_none()
                        
                        if db_user:
                            # Пытаемся создать событие из распознанной речи
                            event_result = await event_manager.process_text(transcribed_text, message.from_user.id, session)
                            
                            if event_result['type'] == 'created':
                                response_text += "🎉 <b>Событие автоматически создано!</b>\n\n"
                                response_text += event_result['message']
                                
                                # Отправляем результат с клавиатурой события
                                await status_msg.edit_text(
                                    response_text,
                                    parse_mode="HTML",
                                    reply_markup=event_result.get('keyboard')
                                )
                                return
                            elif event_result['type'] == 'response':
                                response_text += f"🤖 <b>GPT ответ:</b>\n{event_result['message']}\n\n"
                            else:
                                response_text += "🤔 <b>Не удалось определить событие</b>\n\n"
                                response_text += "💡 Попробуйте сказать более конкретно:\n"
                                response_text += "• «Встреча завтра в 15:00»\n"
                                response_text += "• «Звонок клиенту сегодня в 17:30»\n\n"
                        
                    except Exception as e:
                        logger.warning(f"Failed to auto-create event from voice: {e}")
                        response_text += "⚠️ <b>Событие не создано</b>\n\n"
                
                else:
                    response_text += "📝 <b>Речь не распознана</b>\n\n💡 Попробуйте говорить более чётко\n\n"

                await status_msg.edit_text(response_text, parse_mode="HTML")

            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            break

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        try:
            await message.answer(
                "❌ <b>Ошибка обработки</b>\n\n"
                "Не удалось обработать голосовое сообщение.\n\n"
                "🔄 Попробуйте ещё раз",
                parse_mode="HTML"
            )
        except:
            pass

def register_handlers(dp: Router) -> None:
    """Регистрация обработчиков"""
    dp.include_router(router) 