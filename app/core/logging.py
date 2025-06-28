"""
Система логирования и мониторинга
"""
import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
import time
import functools

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON форматтер для логов"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавление дополнительных полей
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'chat_id'):
            log_entry['chat_id'] = record.chat_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        # Добавление исключения
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class TelegramLogHandler(logging.Handler):
    """Хендлер для отправки логов в Telegram"""
    
    def __init__(self, bot, chat_id: int, level=logging.ERROR):
        super().__init__(level)
        self.bot = bot
        self.chat_id = chat_id
        self.queue = asyncio.Queue()
        self.task = None
    
    def emit(self, record):
        try:
            # Добавление записи в очередь
            asyncio.create_task(self.queue.put(record))
        except Exception:
            self.handleError(record)
    
    async def start(self):
        """Запуск обработчика очереди"""
        self.task = asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """Остановка обработчика"""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _process_queue(self):
        """Обработка очереди логов"""
        while True:
            try:
                record = await self.queue.get()
                await self._send_log(record)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing log queue: {e}")
    
    async def _send_log(self, record):
        """Отправка лога в Telegram"""
        try:
            message = self.format(record)
            
            # Ограничение длины сообщения
            if len(message) > 4000:
                message = message[:4000] + "..."
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"🚨 **Лог ошибки**\n\n{message}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send log to Telegram: {e}")


class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self):
        self.metrics = {}
        self.counters = {}
        self.timers = {}
    
    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Увеличение счетчика"""
        key = self._get_metric_key(metric_name, tags)
        if key not in self.counters:
            self.counters[key] = 0
        self.counters[key] += value
    
    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Установка значения метрики"""
        key = self._get_metric_key(metric_name, tags)
        self.metrics[key] = value
    
    def timer(self, metric_name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Запись времени выполнения"""
        key = self._get_metric_key(metric_name, tags)
        if key not in self.timers:
            self.timers[key] = []
        self.timers[key].append(duration)
    
    def _get_metric_key(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Получение ключа метрики"""
        if tags:
            tag_str = ",".join([f"{k}={v}" for k, v in sorted(tags.items())])
            return f"{metric_name}:{tag_str}"
        return metric_name
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        result = {
            "counters": self.counters.copy(),
            "gauges": self.metrics.copy(),
            "timers": {}
        }
        
        # Вычисление статистики для таймеров
        for key, values in self.timers.items():
            if values:
                result["timers"][key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "sum": sum(values)
                }
        
        return result
    
    def reset(self):
        """Сброс метрик"""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()


# Глобальный сборщик метрик
metrics = MetricsCollector()


def log_execution_time(func):
    """Декоратор для логирования времени выполнения"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Логирование успешного выполнения
            logger.info(
                f"Function {func.__name__} executed successfully",
                extra={
                    'duration': duration,
                    'function': func.__name__,
                    'module': func.__module__
                }
            )
            
            # Запись метрики
            metrics.timer(f"{func.__module__}.{func.__name__}.duration", duration)
            metrics.increment(f"{func.__module__}.{func.__name__}.calls")
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Логирование ошибки
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                extra={
                    'duration': duration,
                    'function': func.__name__,
                    'module': func.__module__,
                    'error': str(e)
                },
                exc_info=True
            )
            
            # Запись метрики ошибки
            metrics.increment(f"{func.__module__}.{func.__name__}.errors")
            
            raise
    
    return wrapper


class RequestLogger:
    """Логгер для HTTP запросов"""
    
    def __init__(self, logger_name: str = "http"):
        self.logger = logging.getLogger(logger_name)
    
    async def log_request(self, request, response=None, duration=None, error=None):
        """Логирование HTTP запроса"""
        log_data = {
            'method': request.method,
            'url': str(request.url),
            'headers': dict(request.headers),
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
        }
        
        if response:
            log_data.update({
                'status_code': response.status_code,
                'response_size': len(response.body) if hasattr(response, 'body') else 0
            })
        
        if duration:
            log_data['duration'] = duration
        
        if error:
            log_data['error'] = str(error)
            self.logger.error("HTTP Request failed", extra=log_data)
        else:
            self.logger.info("HTTP Request", extra=log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "json",
    telegram_bot = None,
    telegram_chat_id: Optional[int] = None
):
    """Настройка системы логирования"""
    
    # Создание директории для логов
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очистка существующих хендлеров
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Настройка форматтера
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Хендлер для файла
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Хендлер для Telegram
    if telegram_bot and telegram_chat_id:
        telegram_handler = TelegramLogHandler(telegram_bot, telegram_chat_id)
        telegram_handler.setFormatter(formatter)
        root_logger.addHandler(telegram_handler)
        
        # Запуск обработчика
        asyncio.create_task(telegram_handler.start())
    
    # Настройка логгеров для внешних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info("Logging system initialized", extra={
        'log_level': log_level,
        'log_file': log_file,
        'log_format': log_format
    })


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.start_time = time.time()
        self.requests_count = 0
        self.errors_count = 0
        self.active_connections = 0
    
    def record_request(self, success: bool = True):
        """Запись запроса"""
        self.requests_count += 1
        if not success:
            self.errors_count += 1
    
    def get_uptime(self) -> float:
        """Получение времени работы"""
        return time.time() - self.start_time
    
    def get_error_rate(self) -> float:
        """Получение процента ошибок"""
        if self.requests_count == 0:
            return 0.0
        return (self.errors_count / self.requests_count) * 100
    
    def get_requests_per_second(self) -> float:
        """Получение запросов в секунду"""
        uptime = self.get_uptime()
        if uptime == 0:
            return 0.0
        return self.requests_count / uptime


# Глобальный монитор производительности
performance_monitor = PerformanceMonitor()


@asynccontextmanager
async def log_context(
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    request_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """Контекстный менеджер для логирования"""
    # Установка контекста в текущую задачу
    task = asyncio.current_task()
    if task:
        task.set_name(f"request_{request_id or 'unknown'}")
    
    # Логирование начала контекста
    logger = logging.getLogger()
    logger.info("Context started", extra={
        'user_id': user_id,
        'chat_id': chat_id,
        'request_id': request_id,
        'extra_data': extra_data
    })
    
    try:
        yield
    except Exception as e:
        # Логирование ошибки
        logger.error("Context error", extra={
            'user_id': user_id,
            'chat_id': chat_id,
            'request_id': request_id,
            'error': str(e),
            'extra_data': extra_data
        }, exc_info=True)
        raise
    finally:
        # Логирование завершения контекста
        logger.info("Context finished", extra={
            'user_id': user_id,
            'chat_id': chat_id,
            'request_id': request_id,
            'extra_data': extra_data
        }) 