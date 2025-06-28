from celery import Celery
from app.config import settings

# Создаем Celery приложение
celery_app = Celery(
    "realestate_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.notification_tasks", 
        "app.tasks.cleanup_tasks"
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_routes={
        'app.tasks.ai_tasks.*': {'queue': 'ai'},
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
        'app.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    },
    beat_schedule={
        'send-reminders': {
            'task': 'app.tasks.notification_tasks.send_event_reminders',
            'schedule': 60.0,  # каждую минуту
        },
        'cleanup-old-files': {
            'task': 'app.tasks.cleanup_tasks.cleanup_old_temp_files',
            'schedule': 3600.0,  # каждый час
        },
    }
)
