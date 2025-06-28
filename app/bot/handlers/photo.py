"""
Упрощённый обработчик изображений
Только OCR + создание событий
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

@router.message(F.photo)
async def handle_photo_message(message: Message):
    """Упрощённый обработчик фотографий"""
    
    try:
        async for session in get_async_session():
            # Начальное сообщение
            status_msg = await message.answer(
                "📷 <b>Изображение получено</b>\n\n"
                "🔄 Распознаю текст...",
                parse_mode="HTML"
            )
            
            # Сохраняем изображение во временный файл
            photo = message.photo[-1]  # Берём самое большое фото
            file_info = await message.bot.get_file(photo.file_id)
            
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                await message.bot.download_file(file_info.file_path, temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Обновляем статус
                await status_msg.edit_text(
                    "📷 <b>Обрабатываю изображение...</b>\n\n"
                    "✅ Изображение загружено\n"
                    "👁️ Распознаю текст...",
                    parse_mode="HTML"
                )

                # Инициализируем AI сервис
                ai_service = AIService()
                
                # Обрабатываем изображение
                result = await ai_service.process_image(temp_file_path)
                
                if "error" in result:
                    await status_msg.edit_text(
                        f"❌ <b>Ошибка обработки</b>\n\n"
                        f"Не удалось обработать изображение: {result['error']}\n\n"
                        "💡 Попробуйте более чёткое изображение",
                        parse_mode="HTML"
                    )
                    return

                # Получаем данные
                extracted_text = result.get("extracted_text", "")
                
                # Обновляем статус
                await status_msg.edit_text(
                    "📷 <b>Обрабатываю изображение...</b>\n\n"
                    "✅ Изображение загружено\n"
                    "✅ Текст распознан\n"
                    "🤖 Создаю событие...",
                    parse_mode="HTML"
                )

                # Формируем ответ
                response_text = "📸 <b>Изображение обработано</b>\n\n"
                
                if extracted_text:
                    # Показываем первые 300 символов
                    preview_text = extracted_text[:300]
                    if len(extracted_text) > 300:
                        preview_text += "..."
                    
                    response_text += f"📝 <b>Распознанный текст:</b>\n{preview_text}\n\n"
                    
                    # 🎯 АВТОМАТИЧЕСКОЕ СОЗДАНИЕ СОБЫТИЯ ИЗ ТЕКСТА ИЗОБРАЖЕНИЯ
                    try:
                        from app.bot.handlers.text import EventManager
                        event_manager = EventManager()
                        
                        # Получаем пользователя из БД
                        from sqlalchemy import select
                        from app.models.user import User
                        result_user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
                        db_user = result_user.scalar_one_or_none()
                        
                        if db_user:
                            # Пытаемся создать событие из распознанного текста
                            event_result = await event_manager.process_text(extracted_text, message.from_user.id, session)
                            
                            if event_result['type'] == 'created':
                                response_text += "🎉 <b>Событие автоматически создано из изображения!</b>\n\n"
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
                                response_text += "🤔 <b>Событие не определено</b>\n\n"
                                response_text += "💡 Возможно, на изображении нет информации о встречах\n\n"
                        
                    except Exception as e:
                        logger.warning(f"Failed to auto-create event from image text: {e}")
                        response_text += "⚠️ <b>Событие не создано автоматически</b>\n\n"
                
                else:
                    response_text += "📝 <b>Текст не обнаружен</b>\n\n"

                await status_msg.edit_text(response_text, parse_mode="HTML")

            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            break

    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        try:
            await message.answer(
                "❌ <b>Ошибка обработки</b>\n\n"
                "Не удалось обработать изображение.\n\n"
                "🔄 Попробуйте ещё раз",
                parse_mode="HTML"
            )
        except:
            pass

@router.message(F.document)
async def handle_document_message(message: Message):
    """Обработчик документов (только изображения)"""
    
    try:
        # Проверяем, что это изображение
        if not message.document or not message.document.mime_type or not message.document.mime_type.startswith('image/'):
            await message.answer(
                "📄 Поддерживаются только изображения.\n\n"
                "💡 Отправьте фото или изображение в виде документа.",
                parse_mode="HTML"
            )
            return
        
        # Обрабатываем как обычное фото
        await handle_photo_message(message)
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        await message.answer(
            "❌ Ошибка обработки документа",
            parse_mode="HTML"
        )

def register_handlers(dp: Router) -> None:
    """Регистрация обработчиков"""
    dp.include_router(router) 