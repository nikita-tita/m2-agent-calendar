import os
import logging
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from pathlib import Path

logger = logging.getLogger(__name__)

@shared_task(name="cleanup_old_temp_files")
def cleanup_old_temp_files():
    """
    Очищает старые временные файлы
    Запускается по расписанию каждый час
    """
    try:
        temp_dir = Path("temp")
        if not temp_dir.exists():
            logger.info("Temp directory does not exist")
            return
        
        # Удаляем файлы старше 2 часов
        cutoff_time = datetime.now() - timedelta(hours=2)
        deleted_count = 0
        
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                try:
                    # Получаем время модификации файла
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        return {"deleted_files": deleted_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise

@shared_task(name="cleanup_large_files")
def cleanup_large_files(max_size_mb: int = 50):
    """
    Удаляет слишком большие временные файлы
    """
    try:
        temp_dir = Path("temp")
        if not temp_dir.exists():
            return
        
        max_size_bytes = max_size_mb * 1024 * 1024
        deleted_count = 0
        
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.stat().st_size > max_size_bytes:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted large file: {file_path} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
                        
                except Exception as e:
                    logger.error(f"Error checking file size {file_path}: {e}")
        
        return {"deleted_large_files": deleted_count}
        
    except Exception as e:
        logger.error(f"Error in large file cleanup: {e}")
        raise

@shared_task(name="optimize_database") 
def optimize_database():
    """
    Выполняет оптимизацию базы данных
    """
    import asyncio
    from sqlalchemy import text
    from app.database import get_async_session
    
    async def _optimize():
        try:
            async for session in get_async_session():
                # VACUUM для PostgreSQL
                await session.execute(text("VACUUM ANALYZE"))
                
                # Обновляем статистику
                await session.execute(text("ANALYZE"))
                
                logger.info("Database optimization completed")
                break
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    return asyncio.run(_optimize())

@shared_task(name="generate_analytics_cache")
def generate_analytics_cache():
    """
    Предварительно генерирует кэш для аналитики
    """
    import asyncio
    from app.services.analytics_service import AnalyticsService
    
    async def _generate_cache():
        try:
            analytics = AnalyticsService()
            
            # Генерируем популярные отчёты
            # await analytics.get_user_activity_stats()
            # await analytics.get_popular_event_types()
            
            logger.info("Analytics cache generated")
            
        except Exception as e:
            logger.error(f"Analytics cache generation failed: {e}")
    
    return asyncio.run(_generate_cache()) 