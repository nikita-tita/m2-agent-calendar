"""
Система оптимизации базы данных
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, create_engine, Index, Table, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from contextlib import asynccontextmanager
from functools import wraps
import json

from app.config import settings
from app.core.cache import cache_service
from app.core.logging import metrics

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Оптимизатор базы данных"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self.sync_engine = None
        self.sync_session_maker = None
        self.query_cache = {}
        self.slow_queries = []
        self.connection_pool_stats = {}
    
    async def initialize(self):
        """Инициализация оптимизатора"""
        # Асинхронный движок с пулом соединений
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Синхронный движок для миграций и индексов
        sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
        self.sync_engine = create_engine(
            sync_url,
            echo=settings.DEBUG,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30
        )
        
        self.sync_session_maker = sessionmaker(
            bind=self.sync_engine,
            expire_on_commit=False
        )
        
        # Создание индексов
        await self.create_indexes()
        
        # Настройка мониторинга
        await self.setup_monitoring()
        
        logger.info("Database optimizer initialized")
    
    async def create_indexes(self):
        """Создание индексов для оптимизации"""
        try:
            # Индексы для пользователей
            indexes = [
                # Пользователи
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
                
                # Недвижимость
                "CREATE INDEX IF NOT EXISTS idx_properties_user_id ON properties(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(type)",
                "CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status)",
                "CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price)",
                "CREATE INDEX IF NOT EXISTS idx_properties_area ON properties(area)",
                "CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(latitude, longitude)",
                "CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_properties_updated_at ON properties(updated_at)",
                
                # Календарь
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_end_time ON calendar_events(end_time)",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_type ON calendar_events(type)",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON calendar_events(status)",
                
                # Напоминания
                "CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_reminders_event_id ON reminders(event_id)",
                "CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_at ON reminders(scheduled_at)",
                "CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)",
                
                # Аналитика
                "CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(type)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics(created_at)",
                
                # API токены
                "CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_api_tokens_token_hash ON api_tokens(token_hash)",
                "CREATE INDEX IF NOT EXISTS idx_api_tokens_expires_at ON api_tokens(expires_at)",
                
                # Составные индексы
                "CREATE INDEX IF NOT EXISTS idx_properties_user_type ON properties(user_id, type)",
                "CREATE INDEX IF NOT EXISTS idx_properties_user_status ON properties(user_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_user_time ON calendar_events(user_id, start_time)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_user_type_date ON analytics(user_id, type, date)",
            ]
            
            async with self.engine.begin() as conn:
                for index_sql in indexes:
                    try:
                        await conn.execute(text(index_sql))
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def setup_monitoring(self):
        """Настройка мониторинга базы данных"""
        # Запуск периодического сбора статистики
        asyncio.create_task(self._monitor_database_performance())
    
    async def _monitor_database_performance(self):
        """Мониторинг производительности базы данных"""
        while True:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                
                # Сбор статистики пула соединений
                pool = self.engine.pool
                self.connection_pool_stats = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
                
                # Запись метрик
                metrics.gauge("database.pool.size", pool.size())
                metrics.gauge("database.pool.checked_in", pool.checkedin())
                metrics.gauge("database.pool.checked_out", pool.checkedout())
                metrics.gauge("database.pool.overflow", pool.overflow())
                
                # Анализ медленных запросов
                await self._analyze_slow_queries()
                
                # Очистка кэша запросов
                await self._cleanup_query_cache()
                
            except Exception as e:
                logger.error(f"Database monitoring error: {e}")
    
    async def _analyze_slow_queries(self):
        """Анализ медленных запросов"""
        if len(self.slow_queries) > 100:
            # Оставляем только последние 50 запросов
            self.slow_queries = self.slow_queries[-50:]
        
        # Логирование медленных запросов
        for query in self.slow_queries:
            if query["duration"] > 1.0:  # Больше 1 секунды
                logger.warning(f"Slow query detected: {query}")
    
    async def _cleanup_query_cache(self):
        """Очистка кэша запросов"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.query_cache.items():
            if current_time - data["timestamp"] > 3600:  # 1 час
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.query_cache[key]
    
    @asynccontextmanager
    async def get_session(self):
        """Получение сессии базы данных с мониторингом"""
        session = None
        start_time = time.time()
        
        try:
            session = self.async_session_maker()
            yield session
        except SQLAlchemyError as e:
            duration = time.time() - start_time
            logger.error(f"Database error: {e} (duration: {duration:.3f}s)")
            metrics.increment("database.errors")
            raise
        finally:
            if session:
                duration = time.time() - start_time
                metrics.timer("database.session.duration", duration)
                await session.close()
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None, cache: bool = True) -> List[Dict[str, Any]]:
        """Выполнение запроса с кэшированием и мониторингом"""
        start_time = time.time()
        
        # Создание ключа кэша
        cache_key = None
        if cache:
            cache_key = f"query:{hash(query + str(params))}"
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                metrics.increment("database.cache.hits")
                return cached_result
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]
                
                duration = time.time() - start_time
                
                # Запись метрик
                metrics.timer("database.query.duration", duration)
                metrics.increment("database.queries")
                
                # Кэширование результата
                if cache and cache_key and duration < 0.1:  # Кэшируем только быстрые запросы
                    await cache_service.set(cache_key, rows, expire=300)  # 5 минут
                
                # Запись медленных запросов
                if duration > 0.5:  # Больше 500ms
                    self.slow_queries.append({
                        "query": query,
                        "params": params,
                        "duration": duration,
                        "timestamp": time.time()
                    })
                
                return rows
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Query execution error: {e} (duration: {duration:.3f}s)")
            metrics.increment("database.query.errors")
            raise
    
    async def bulk_insert(self, table_name: str, data: List[Dict[str, Any]]) -> int:
        """Массовая вставка данных"""
        if not data:
            return 0
        
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                # Подготовка данных для вставки
                columns = list(data[0].keys())
                values = [tuple(row[col] for col in columns) for row in data]
                
                # SQL для массовой вставки
                placeholders = ", ".join([f":{i}" for i in range(len(columns))])
                columns_str = ", ".join(columns)
                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                # Выполнение вставки
                result = await session.execute(text(sql), values)
                await session.commit()
                
                duration = time.time() - start_time
                metrics.timer("database.bulk_insert.duration", duration)
                metrics.increment("database.bulk_inserts")
                
                return len(data)
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Bulk insert error: {e} (duration: {duration:.3f}s)")
            metrics.increment("database.bulk_insert.errors")
            raise
    
    async def optimize_table(self, table_name: str) -> Dict[str, Any]:
        """Оптимизация таблицы"""
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                # Анализ таблицы
                await session.execute(text(f"ANALYZE {table_name}"))
                
                # Очистка таблицы (если PostgreSQL)
                if "postgresql" in settings.DATABASE_URL:
                    await session.execute(text(f"VACUUM {table_name}"))
                
                await session.commit()
                
                duration = time.time() - start_time
                
                result = {
                    "table": table_name,
                    "duration": duration,
                    "status": "success"
                }
                
                metrics.timer("database.optimize.duration", duration)
                metrics.increment("database.optimizations")
                
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Table optimization error: {e}")
            metrics.increment("database.optimize.errors")
            
            return {
                "table": table_name,
                "duration": duration,
                "status": "error",
                "error": str(e)
            }
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        try:
            async with self.get_session() as session:
                # Размер базы данных
                size_result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """))
                db_size = size_result.scalar()
                
                # Количество записей в таблицах
                tables_result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """))
                tables_stats = [dict(row._mapping) for row in tables_result]
                
                # Статистика индексов
                indexes_result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """))
                indexes_stats = [dict(row._mapping) for row in indexes_result]
                
                return {
                    "database_size": db_size,
                    "tables_stats": tables_stats,
                    "indexes_stats": indexes_stats,
                    "connection_pool": self.connection_pool_stats,
                    "slow_queries_count": len(self.slow_queries),
                    "query_cache_size": len(self.query_cache)
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, table_name: str, date_column: str, days: int) -> int:
        """Очистка старых данных"""
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                # Удаление старых записей
                sql = f"""
                    DELETE FROM {table_name} 
                    WHERE {date_column} < NOW() - INTERVAL '{days} days'
                """
                
                result = await session.execute(text(sql))
                await session.commit()
                
                deleted_count = result.rowcount
                duration = time.time() - start_time
                
                logger.info(f"Cleaned up {deleted_count} old records from {table_name}")
                
                metrics.timer("database.cleanup.duration", duration)
                metrics.increment("database.cleanup.records", deleted_count)
                
                return deleted_count
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Data cleanup error: {e}")
            metrics.increment("database.cleanup.errors")
            raise


def query_monitor(func):
    """Декоратор для мониторинга запросов"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Запись метрик
            metrics.timer(f"{func.__module__}.{func.__name__}.duration", duration)
            metrics.increment(f"{func.__module__}.{func.__name__}.calls")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.increment(f"{func.__module__}.{func.__name__}.errors")
            logger.error(f"Query error in {func.__name__}: {e}")
            raise
    
    return wrapper


class QueryBuilder:
    """Построитель оптимизированных запросов"""
    
    @staticmethod
    def build_property_search_query(
        user_id: Optional[int] = None,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[str, Dict[str, Any]]:
        """Построение запроса поиска недвижимости"""
        
        conditions = []
        params = {}
        
        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        
        if property_type:
            conditions.append("type = :property_type")
            params["property_type"] = property_type
        
        if min_price is not None:
            conditions.append("price >= :min_price")
            params["min_price"] = min_price
        
        if max_price is not None:
            conditions.append("price <= :max_price")
            params["max_price"] = max_price
        
        if location:
            conditions.append("address ILIKE :location")
            params["location"] = f"%{location}%"
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM properties 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        return query, params
    
    @staticmethod
    def build_calendar_events_query(
        user_id: int,
        start_date: str,
        end_date: str,
        event_type: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Построение запроса событий календаря"""
        
        conditions = ["user_id = :user_id"]
        params = {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        }
        
        if event_type:
            conditions.append("type = :event_type")
            params["event_type"] = event_type
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM calendar_events 
            WHERE {where_clause}
            AND start_time >= :start_date 
            AND start_time <= :end_date
            ORDER BY start_time ASC
        """
        
        return query, params


# Глобальный экземпляр оптимизатора
db_optimizer = DatabaseOptimizer() 