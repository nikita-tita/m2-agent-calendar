import logging
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.event import Event
from app.models.user import User

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="send_event_reminders")
def send_event_reminders(self):
    """
    Отправляет напоминания о предстоящих событиях
    Аналог уведомлений в Dola.ai
    """
    import asyncio
    
    async def _send_reminders():
        try:
            async for session in get_async_session():
                # Ищем события на ближайший час которые нуждаются в напоминании
                now = datetime.now()
                reminder_time = now + timedelta(minutes=60)  # За час до события
                
                query = select(Event).join(User).where(
                    Event.start_time <= reminder_time,
                    Event.start_time > now,
                    Event.is_reminder_sent == False,
                    User.reminder_enabled == True
                )
                
                result = await session.execute(query)
                events = result.scalars().all()
                
                sent_count = 0
                for event in events:
                    try:
                        # Отправляем напоминание через бота
                        await send_single_reminder.delay(event.id)
                        
                        # Помечаем как отправленное
                        event.is_reminder_sent = True
                        await session.commit()
                        sent_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send reminder for event {event.id}: {e}")
                
                logger.info(f"Sent {sent_count} event reminders")
                break
                
        except Exception as e:
            logger.error(f"Error in send_event_reminders: {e}")
            raise self.retry(countdown=60, max_retries=3)
    
    # Запускаем async функцию
    asyncio.run(_send_reminders())

@shared_task(name="send_single_reminder")
def send_single_reminder(event_id: int):
    """
    Отправляет одно напоминание о событии
    """
    import asyncio
    from aiogram import Bot
    from app.config import settings
    
    async def _send_reminder():
        try:
            async for session in get_async_session():
                # Получаем событие
                result = await session.execute(
                    select(Event).join(User).where(Event.id == event_id)
                )
                event = result.scalar_one_or_none()
                
                if not event:
                    logger.warning(f"Event {event_id} not found")
                    return
                
                # Формируем сообщение напоминания
                time_until = event.start_time - datetime.now()
                minutes_until = int(time_until.total_seconds() / 60)
                
                if minutes_until <= 0:
                    time_text = "сейчас"
                elif minutes_until < 60:
                    time_text = f"через {minutes_until} мин"
                else:
                    hours = minutes_until // 60
                    mins = minutes_until % 60
                    time_text = f"через {hours}ч {mins}мин"
                
                message = f"🔔 **Напоминание о событии**\n\n"
                message += f"📅 {event.title}\n"
                message += f"🕒 {event.start_time.strftime('%H:%M')} ({time_text})\n"
                
                if event.location:
                    message += f"📍 {event.location}\n"
                
                if hasattr(event, 'client_name') and event.client_name:
                    message += f"👤 {event.client_name}\n"
                
                message += f"\n💡 Не забудьте подготовиться к встрече!"
                
                # Отправляем через бота
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=event.user.telegram_id,
                    text=message,
                    parse_mode="HTML"
                )
                await bot.session.close()
                
                logger.info(f"Reminder sent for event {event_id}")
                break
                
        except Exception as e:
            logger.error(f"Error sending reminder for event {event_id}: {e}")
            raise
    
    asyncio.run(_send_reminder())

@shared_task(name="send_daily_schedule") 
def send_daily_schedule(user_id: int):
    """
    Отправляет ежедневное расписание пользователю
    Аналог daily digest в Dola.ai
    """
    import asyncio
    from aiogram import Bot
    from app.config import settings
    
    async def _send_schedule():
        try:
            async for session in get_async_session():
                # Получаем пользователя
                user_result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user or not user.daily_digest_enabled:
                    return
                
                # Получаем события на сегодня
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                events_result = await session.execute(
                    select(Event).where(
                        Event.user_id == user_id,
                        Event.start_time >= today_start,
                        Event.start_time < today_end
                    ).order_by(Event.start_time)
                )
                events = events_result.scalars().all()
                
                if not events:
                    message = "📅 **Ваше расписание на сегодня**\n\n🎉 У вас свободный день!"
                else:
                    message = f"📅 **Ваше расписание на сегодня ({len(events)} событий)**\n\n"
                    
                    for event in events:
                        message += f"🕒 {event.start_time.strftime('%H:%M')} - {event.title}\n"
                        if event.location:
                            message += f"   📍 {event.location}\n"
                        message += "\n"
                
                message += f"\n✨ Продуктивного дня!"
                
                # Отправляем через бота
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode="HTML"
                )
                await bot.session.close()
                
                logger.info(f"Daily schedule sent to user {user_id}")
                break
                
        except Exception as e:
            logger.error(f"Error sending daily schedule to user {user_id}: {e}")
    
    asyncio.run(_send_schedule())

@shared_task(name="process_ai_task")
def process_ai_task(task_type: str, data: dict):
    """
    Обрабатывает AI задачи асинхронно
    Для тяжелых операций вроде OCR, больших аудио файлов
    """
    import asyncio
    
    async def _process_ai():
        try:
            if task_type == "speech_to_text":
                from app.ai.speech.whisper_client import WhisperClient
                
                whisper = WhisperClient()
                result = await whisper.transcribe_file(data['file_path'])
                return result
                
            elif task_type == "ocr_processing":
                from app.ai.vision.ocr_client import OCRClient
                
                ocr = OCRClient()
                result = await ocr.extract_text(data['image_path'])
                return result
                
            elif task_type == "gpt_analysis":
                from app.ai.nlp.gpt_client import GPTClient
                from app.config import settings
                
                if settings.OPENAI_API_KEY:
                    gpt = GPTClient(settings.OPENAI_API_KEY)
                    result = await gpt.parse_calendar_event(data['text'])
                    return result
                
            logger.warning(f"Unknown AI task type: {task_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing AI task {task_type}: {e}")
            raise
    
    return asyncio.run(_process_ai()) 