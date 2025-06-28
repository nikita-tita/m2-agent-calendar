import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_async_session
from app.models.event import Event

logger = logging.getLogger(__name__)

class VectorSearchService:
    """
    Сервис семантического поиска по событиям
    Аналог векторного поиска в Dola.ai для понимания контекста
    """
    
    def __init__(self):
        """Инициализация модели для эмбеддингов"""
        try:
            # Используем многоязычную модель для русского языка
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.embedding_dimension = 384
            logger.info("Vector search service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector search: {e}")
            self.model = None
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Создает векторное представление текста
        
        Args:
            text: Текст для векторизации
            
        Returns:
            Вектор эмбеддинга или None при ошибке
        """
        if not self.model:
            return None
            
        try:
            # Нормализуем текст
            clean_text = text.strip().lower()
            if not clean_text:
                return None
            
            # Создаем эмбеддинг
            embedding = self.model.encode(clean_text)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return None
    
    async def add_event_embedding(self, event_id: int, title: str, description: Optional[str] = None):
        """Добавляет эмбеддинг для события"""
        try:
            # Формируем контент для эмбеддинга
            content = title
            if description:
                content += f" {description}"
            
            # Получаем эмбеддинг
            embedding = await self.get_embedding(content)
            
            # Сохраняем в базу как JSON строку
            embedding_json = json.dumps(embedding)
            
            async for session in get_async_session():
                await session.execute(text("""
                    INSERT INTO event_embeddings (event_id, embedding, content)
                    VALUES (:event_id, :embedding, :content)
                    ON CONFLICT (event_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        content = EXCLUDED.content,
                        updated_at = NOW()
                """), {
                    'event_id': event_id,
                    'embedding': embedding_json,  # Сохраняем как JSON строку
                    'content': content
                })
                await session.commit()
                break
                
        except Exception as e:
            logger.error(f"Error adding event embedding: {e}")
            # Не останавливаем выполнение, если эмбеддинг не сохранился
    
    async def search_similar_events(
        self, 
        query: str, 
        user_id: int, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Ищет похожие события по семантическому сходству
        
        Args:
            query: Поисковый запрос
            user_id: ID пользователя
            limit: Максимальное количество результатов
            similarity_threshold: Минимальный порог сходства
            
        Returns:
            Список похожих событий с оценками сходства
        """
        if not self.model:
            logger.warning("Vector search not available")
            return []
        
        try:
            # Создаем эмбеддинг запроса
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Поиск в векторной БД
            async for session in get_async_session():
                result = await session.execute(
                    text("""
                        SELECT 
                            e.id,
                            e.title,
                            e.description,
                            e.start_time,
                            e.location,
                            ee.content,
                            1 - (ee.embedding <=> :query_embedding) as similarity
                        FROM events e
                        JOIN event_embeddings ee ON e.id = ee.event_id
                        WHERE e.user_id = :user_id
                            AND 1 - (ee.embedding <=> :query_embedding) > :threshold
                        ORDER BY similarity DESC
                        LIMIT :limit
                    """),
                    {
                        "query_embedding": query_embedding,
                        "user_id": user_id,
                        "threshold": similarity_threshold,
                        "limit": limit
                    }
                )
                
                events = []
                for row in result:
                    events.append({
                        "id": row.id,
                        "title": row.title,
                        "description": row.description,
                        "start_time": row.start_time,
                        "location": row.location,
                        "content": row.content,
                        "similarity": float(row.similarity)
                    })
                
                logger.debug(f"Found {len(events)} similar events for query: {query}")
                break
            
            return events
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def suggest_related_events(
        self, 
        event_text: str, 
        user_id: int, 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Предлагает связанные события на основе контекста
        Аналог Smart Suggestions в Dola.ai
        
        Args:
            event_text: Текст события для анализа
            user_id: ID пользователя
            limit: Количество предложений
            
        Returns:
            Список связанных событий
        """
        try:
            # Используем семантический поиск для поиска похожих событий
            similar_events = await self.search_similar_events(
                query=event_text,
                user_id=user_id,
                limit=limit * 2,  # Берем больше для фильтрации
                similarity_threshold=0.5
            )
            
            # Фильтруем и ранжируем предложения
            suggestions = []
            for event in similar_events[:limit]:
                suggestions.append({
                    "title": event["title"],
                    "reason": f"Похоже на это событие (сходство: {event['similarity']:.1%})",
                    "similarity": event["similarity"],
                    "event_id": event["id"]
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating event suggestions: {e}")
            return []
    
    async def analyze_event_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        Анализирует паттерны в событиях пользователя
        Для предсказания типичных встреч и времени
        """
        try:
            async for session in get_async_session():
                # Получаем все события пользователя с эмбеддингами
                result = await session.execute(
                    text("""
                        SELECT 
                            e.event_type,
                            e.location,
                            EXTRACT(HOUR FROM e.start_time) as hour,
                            EXTRACT(DOW FROM e.start_time) as day_of_week,
                            ee.embedding
                        FROM events e
                        JOIN event_embeddings ee ON e.id = ee.event_id
                        WHERE e.user_id = :user_id
                            AND e.start_time > NOW() - INTERVAL '30 days'
                        ORDER BY e.start_time DESC
                    """),
                    {"user_id": user_id}
                )
                
                events_data = result.fetchall()
                break
            
            if not events_data:
                return {"patterns": [], "recommendations": []}
            
            # Анализируем паттерны
            patterns = {
                "common_types": {},
                "preferred_times": {},
                "frequent_locations": {},
                "weekly_distribution": {}
            }
            
            for event in events_data:
                # Подсчет типов событий
                event_type = event.event_type or "other"
                patterns["common_types"][event_type] = patterns["common_types"].get(event_type, 0) + 1
                
                # Популярные часы
                hour = int(event.hour)
                patterns["preferred_times"][hour] = patterns["preferred_times"].get(hour, 0) + 1
                
                # Частые локации
                if event.location:
                    patterns["frequent_locations"][event.location] = patterns["frequent_locations"].get(event.location, 0) + 1
                
                # Распределение по дням недели
                dow = int(event.day_of_week)
                patterns["weekly_distribution"][dow] = patterns["weekly_distribution"].get(dow, 0) + 1
            
            # Генерируем рекомендации
            recommendations = []
            
            # Рекомендуем самый частый тип события
            if patterns["common_types"]:
                most_common_type = max(patterns["common_types"], key=patterns["common_types"].get)
                recommendations.append(f"Чаще всего у вас: {most_common_type}")
            
            # Рекомендуем популярное время
            if patterns["preferred_times"]:
                popular_hour = max(patterns["preferred_times"], key=patterns["preferred_times"].get)
                recommendations.append(f"Предпочитаемое время: {popular_hour}:00")
            
            return {
                "patterns": patterns,
                "recommendations": recommendations,
                "total_events": len(events_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing event patterns: {e}")
            return {"patterns": [], "recommendations": []}

    async def get_embedding(self, text: str) -> List[float]:
        """Получает эмбеддинг для текста"""
        try:
            if not self.openai_client:
                logger.warning("OpenAI client not available")
                return []
            
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return [] 