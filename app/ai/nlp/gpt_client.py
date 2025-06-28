import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class GPTClient:
    """Клиент для работы с OpenAI GPT-4"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Args:
            api_key: API ключ OpenAI
            model: Модель GPT для использования
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Системные промпты для разных задач
        self.system_prompts = {
            "real_estate_parser": """Ты - специализированный AI-ассистент для агентов по недвижимости в России. 
Твоя задача - извлекать структурированную информацию из текстов о недвижимости.

Извлекай следующую информацию:
- Тип недвижимости (квартира, дом, коммерческая недвижимость)
- Адрес или район
- Площадь (в кв.м)
- Количество комнат
- Цена (в рублях)
- Этаж
- Описание и особенности
- Контактная информация

Отвечай в формате JSON с полями:
{
    "property_type": "тип недвижимости",
    "address": "адрес или район",
    "area": "площадь в кв.м",
    "rooms": "количество комнат",
    "price": "цена в рублях",
    "floor": "этаж",
    "description": "описание",
    "contact": "контактная информация",
    "confidence": "уверенность в извлечении (0-1)"
}

Если информация не найдена, используй null для соответствующего поля.""",
            
            "event_parser": """Ты - экспертный AI календарный ассистент для агентов недвижимости в России.

СПЕЦИАЛИЗАЦИЯ: недвижимость, встречи с клиентами, показы объектов, звонки.

ЗАДАЧА: Извлечь точную структурированную информацию о событии из естественного языка.

ТИПЫ СОБЫТИЙ:
- meeting: встречи, переговоры, консультации
- call: звонки, созвоны
- showing: показы квартир/домов/объектов
- viewing: просмотры объектов клиентом
- deal: подписание документов, сделки
- task: задачи, напоминания

ВРЕМЕННЫЕ ПАТТЕРНЫ:
- "сегодня" = текущая дата
- "завтра" = текущая дата + 1 день
- "послезавтра" = текущая дата + 2 дня
- "в понедельник" = ближайший понедельник
- "на следующей неделе" = добавить 7 дней к ближайшему дню
- "в 15" = 15:00 (если контекст рабочий день)
- "утром" = 10:00, "днём" = 14:00, "вечером" = 18:00

ОБЯЗАТЕЛЬНЫЙ ФОРМАТ ОТВЕТА (только JSON, без дополнительного текста):
{
    "event_type": "meeting|call|showing|viewing|deal|task",
    "title": "краткий заголовок события",
    "client_name": "имя клиента или null",
    "location": "место встречи или null",
    "date": "YYYY-MM-DD или текстовое описание если неточно",
    "time": "HH:MM в 24-часовом формате или null",
    "duration_minutes": "продолжительность в минутах (по умолчанию 60)",
    "description": "дополнительные детали или null",
    "priority": "high|medium|low",
    "confidence": "0.0-1.0 уверенность в парсинге"
}

ПРИМЕРЫ ПАРСИНГА:

Ввод: "запиши завтра встреча в офисе с Катей в 19"
Вывод: {"event_type": "meeting", "title": "Встреча с Катей", "client_name": "Катя", "location": "офис", "date": "завтра", "time": "19:00", "duration_minutes": 60, "description": null, "priority": "medium", "confidence": 0.95}

Ввод: "звонок клиенту Иванову в понедельник в 14:30"
Вывод: {"event_type": "call", "title": "Звонок Иванову", "client_name": "Иванов", "location": null, "date": "понедельник", "time": "14:30", "duration_minutes": 30, "description": null, "priority": "medium", "confidence": 0.9}

Ввод: "показ трёшки на Арбате завтра утром"
Вывод: {"event_type": "showing", "title": "Показ трёшки на Арбате", "client_name": null, "location": "Арбат", "date": "завтра", "time": "10:00", "duration_minutes": 90, "description": "трёхкомнатная квартира", "priority": "high", "confidence": 0.85}

Ввод: "встреча с Петровыми в офисе завтра в 16"
Вывод: {"event_type": "meeting", "title": "Встреча с Петровыми", "client_name": "Петровы", "location": "офис", "date": "завтра", "time": "16:00", "duration_minutes": 60, "description": null, "priority": "medium", "confidence": 0.9}

ПРАВИЛА:
1. ВСЕГДА отвечай только JSON, без пояснений
2. Для неоднозначного времени предполагай рабочие часы (9:00-18:00)
3. Если уверенность < 0.7, укажи это в confidence
4. Имена клиентов пиши с большой буквы
5. Для показов недвижимости duration_minutes = 90 по умолчанию
6. Если дата неточная, оставляй как текстовое описание
7. Приоритет "high" для показов объектов, "medium" для встреч, "low" для задач

Анализируй текст пользователя и извлекай событие:""",
            
            "calendar_assistant": """Ты - AI-ассистент для планирования встреч с клиентами по недвижимости.
Помогай агентам планировать встречи, учитывая:
- Предпочтения клиента
- Доступность агента
- Логистику (время на дорогу)
- Тип встречи (показ объекта, консультация, подписание документов)

Предлагай оптимальное время и место для встречи.""",
            
            "general_assistant": """Ты - полезный AI-ассистент для агентов по недвижимости.
Отвечай на вопросы о недвижимости, помогай с документами, давай советы по работе с клиентами.
Всегда отвечай на русском языке."""
        }
    
    async def extract_real_estate_info(self, text: str) -> Dict[str, Any]:
        """
        Извлекает информацию о недвижимости из текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            Структурированная информация о недвижимости
        """
        try:
            logger.info("Extracting real estate information from text")
            
            messages = [
                {"role": "system", "content": self.system_prompts["real_estate_parser"]},
                {"role": "user", "content": f"Извлеки информацию о недвижимости из следующего текста:\n\n{text}"}
            ]
            
            response = await self._make_request(messages)
            
            # Парсим JSON ответ
            try:
                result = json.loads(response)
                logger.info("Successfully extracted real estate information")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {"error": "Failed to parse response", "raw_response": response}
                
        except Exception as e:
            logger.error(f"Error in extract_real_estate_info: {e}")
            return {"error": str(e)}
    
    async def suggest_meeting_time(self, client_preferences: str, agent_schedule: str) -> str:
        """
        Предлагает оптимальное время для встречи
        
        Args:
            client_preferences: Предпочтения клиента
            agent_schedule: Расписание агента
            
        Returns:
            Предложение времени встречи
        """
        try:
            logger.info("Suggesting meeting time")
            
            prompt = f"""
Клиент хочет встретиться и указал следующие предпочтения:
{client_preferences}

Расписание агента:
{agent_schedule}

Предложи оптимальное время для встречи, учитывая предпочтения клиента и доступность агента.
"""
            
            messages = [
                {"role": "system", "content": self.system_prompts["calendar_assistant"]},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._make_request(messages)
            logger.info("Meeting time suggestion generated")
            return response
            
        except Exception as e:
            logger.error(f"Error in suggest_meeting_time: {e}")
            return f"Ошибка при планировании встречи: {str(e)}"
    
    async def answer_question(self, question: str, context: str = "") -> str:
        """
        Отвечает на общие вопросы о недвижимости
        
        Args:
            question: Вопрос пользователя
            context: Дополнительный контекст
            
        Returns:
            Ответ на вопрос
        """
        try:
            logger.info("Answering general question")
            
            full_question = question
            if context:
                full_question = f"Контекст: {context}\n\nВопрос: {question}"
            
            messages = [
                {"role": "system", "content": self.system_prompts["general_assistant"]},
                {"role": "user", "content": full_question}
            ]
            
            response = await self._make_request(messages)
            logger.info("Question answered successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return f"Извините, произошла ошибка при обработке вопроса: {str(e)}"
    
    async def _make_request(self, messages: List[Dict[str, str]]) -> str:
        """
        Выполняет запрос к GPT API
        
        Args:
            messages: Список сообщений для отправки
            
        Returns:
            Ответ от модели
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.3,  # Низкая температура для более предсказуемых ответов
                timeout=30
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise Exception("Превышен лимит запросов к OpenAI. Попробуйте позже.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Ошибка API OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _make_request: {e}")
            raise
    
    async def validate_real_estate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидирует и дополняет данные о недвижимости
        
        Args:
            data: Данные о недвижимости
            
        Returns:
            Валидированные и дополненные данные
        """
        try:
            logger.info("Validating real estate data")
            
            # Проверяем обязательные поля
            required_fields = ["property_type", "price", "area"]
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                data["validation_errors"] = f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            
            # Нормализуем данные
            if data.get("price"):
                try:
                    # Убираем все кроме цифр
                    price_str = str(data["price"]).replace(" ", "").replace(",", "")
                    price = int(''.join(filter(str.isdigit, price_str)))
                    data["price_normalized"] = price
                except:
                    data["price_normalized"] = None
            
            if data.get("area"):
                try:
                    area_str = str(data["area"]).replace(" ", "").replace(",", ".")
                    area = float(''.join(c for c in area_str if c.isdigit() or c == '.'))
                    data["area_normalized"] = area
                except:
                    data["area_normalized"] = None
            
            logger.info("Real estate data validation completed")
            return data
            
        except Exception as e:
            logger.error(f"Error in validate_real_estate_data: {e}")
            data["validation_error"] = str(e)
            return data
    
    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о модели"""
        return {
            "model": self.model,
            "api_key_configured": bool(self.api_key),
            "system_prompts_available": list(self.system_prompts.keys()),
            "max_tokens": 2000,
            "temperature": 0.3
        }

    async def parse_calendar_event(self, text: str) -> Dict[str, Any]:
        """
        Парсит событие календаря из текста с помощью GPT
        
        Args:
            text: Текст с описанием события
            
        Returns:
            Структурированная информация о событии
        """
        try:
            from datetime import datetime, timedelta
            import locale
            
            # Получаем контекстную информацию как в Dola.ai
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            
            # Русские названия дней недели
            weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
            weekday = weekdays[now.weekday()]
            
            tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after_tomorrow = (now + timedelta(days=2)).strftime("%Y-%m-%d")
            
            # Находим ближайший понедельник
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:  # Если сегодня понедельник
                days_until_monday = 7
            next_monday = (now + timedelta(days=days_until_monday)).strftime("%Y-%m-%d")
            
            logger.info(f"Parsing calendar event from text: {text}")
            
            # Подготавливаем контекстный промпт с актуальными датами
            contextual_prompt = f"""Ты - экспертный AI календарный ассистент для агентов недвижимости в России.

ТЕКУЩИЙ КОНТЕКСТ:
- Сегодня: {current_date} ({weekday})
- Текущее время: {current_time}
- Завтра: {tomorrow}
- Послезавтра: {day_after_tomorrow}
- Ближайший понедельник: {next_monday}
- Временная зона: Europe/Moscow

СПЕЦИАЛИЗАЦИЯ: недвижимость, встречи с клиентами, показы объектов, звонки.

ТИПЫ СОБЫТИЙ:
- meeting: встречи, переговоры, консультации
- call: звонки, созвоны
- showing: показы квартир/домов/объектов
- viewing: просмотры объектов клиентом
- deal: подписание документов, сделки
- task: задачи, напоминания

ВРЕМЕННЫЕ ПАТТЕРНЫ (с учетом текущей даты):
- "сегодня" → {current_date}
- "завтра" → {tomorrow}
- "послезавтра" → {day_after_tomorrow}
- "в понедельник" → {next_monday}
- "утром" → 10:00, "днём" → 14:00, "вечером" → 18:00

ОБЯЗАТЕЛЬНЫЙ ФОРМАТ ОТВЕТА (только JSON):
{{
    "event_type": "meeting|call|showing|viewing|deal|task",
    "title": "краткий заголовок события",
    "client_name": "имя клиента или null",
    "location": "место встречи или null",
    "date": "YYYY-MM-DD (используй контекст выше)",
    "time": "HH:MM в 24-часовом формате или null",
    "duration_minutes": 60,
    "description": "дополнительные детали или null",
    "priority": "high|medium|low",
    "confidence": "0.0-1.0"
}}

ПРАВИЛА:
1. ТОЛЬКО JSON ответ, без пояснений
2. Используй точные даты из контекста выше
3. Для показов duration_minutes = 90
4. Приоритет: "high" для показов, "medium" для встреч, "low" для задач
5. Если время не указано в рабочий день - предполагай 10:00

Проанализируй и извлеки событие:"""
            
            messages = [
                {"role": "system", "content": contextual_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self._make_request(messages)
            
            # Парсим JSON ответ
            try:
                result = json.loads(response)
                logger.info("Successfully parsed calendar event with context")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {"error": "Failed to parse response", "raw_response": response}
                
        except Exception as e:
            logger.error(f"Error in parse_calendar_event: {e}")
            return {"error": str(e)} 