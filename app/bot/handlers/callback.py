"""
Упрощённый обработчик callback'ов
Только события и помощь
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.database import get_async_session

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Помощь"""
    help_text = (
        "🤖 <b>Как пользоваться ботом</b>\n\n"
        "<b>📝 Создание событий:</b>\n"
        "• «Встреча завтра в 15:00»\n"
        "• «Звонок клиенту сегодня в 17:30»\n"
        "• «Показ квартиры в понедельник»\n\n"
        "<b>🎤 Голосовые сообщения:</b>\n"
        "Просто скажите что планируете\n\n"
        "<b>📸 Фотографии:</b>\n"
        "Пришлите скриншот с датой и временем\n\n"
        "<b>📅 Календарь:</b>\n"
        "Нажмите кнопку «Календарь» для просмотра"
    )
    
    from app.bot.keyboards.inline import get_calendar_keyboard
    await callback.message.edit_text(
        help_text,
        reply_markup=get_calendar_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "help_examples")
async def help_examples_callback(callback: CallbackQuery):
    """Примеры команд"""
    examples_text = (
        "📝 <b>Примеры команд для создания событий</b>\n\n"
        "<b>Простые команды:</b>\n"
        "• Встреча завтра в 15:00\n"
        "• Звонок сегодня в 17:30\n"
        "• Показ в понедельник\n\n"
        "<b>Подробные команды:</b>\n"
        "• Встреча с клиентом Ивановым завтра в 14:00\n"
        "• Звонок по проекту сегодня в 16:00\n"
        "• Показ квартиры в понедельник в 15:30\n\n"
        "<b>Управление событиями:</b>\n"
        "• Удали встречу\n"
        "• Перенеси звонок\n"
        "• Покажи мои события"
    )
    
    from app.bot.keyboards.inline import get_calendar_keyboard
    await callback.message.edit_text(
        examples_text,
        reply_markup=get_calendar_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("event_"))
async def event_callback(callback: CallbackQuery):
    """Обработка действий с событиями"""
    action = callback.data
    
    if action.startswith("event_delete_"):
        event_id = int(action.split("_")[-1])
        
        from app.bot.keyboards.inline import get_event_actions_keyboard
        await callback.message.edit_text(
            f"🗑️ Удалить событие #{event_id}?",
            reply_markup=get_event_actions_keyboard(event_id, "delete"),
            parse_mode="HTML"
        )
        
    elif action.startswith("event_confirm_delete_"):
        event_id = int(action.split("_")[-1])
        
        try:
            async for session in get_async_session():
                from sqlalchemy import select
                from app.models.event import Event
                
                result = await session.execute(select(Event).where(Event.id == event_id))
                event = result.scalar_one_or_none()
                
                if event:
                    await session.delete(event)
                    await session.commit()
                    
                    await callback.message.edit_text(
                        "✅ Событие удалено",
                        parse_mode="HTML"
                    )
                else:
                    await callback.message.edit_text(
                        "❌ Событие не найдено",
                        parse_mode="HTML"
                    )
                break
                
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            await callback.message.edit_text(
                "❌ Ошибка при удалении события",
                parse_mode="HTML"
            )
    
    elif action == "event_cancel_delete":
        await callback.message.edit_text(
            "❌ Удаление отменено",
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "create_event")
async def create_event_callback(callback: CallbackQuery):
    """Создание события"""
    await callback.message.answer(
        "📝 <b>Создание события</b>\n\n"
        "Напишите что хотите запланировать:\n\n"
        "Например:\n"
        "• «Встреча завтра в 15:00»\n"
        "• «Звонок клиенту сегодня в 17:30»",
        parse_mode="HTML"
    )
    await callback.answer()

def register_handlers(dp: Router) -> None:
    """Регистрация обработчиков"""
    dp.include_router(router) 