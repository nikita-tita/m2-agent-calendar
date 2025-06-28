# ТЕХНИЧЕСКОЕ ЗАДАНИЕ: RealEstate Calendar Bot
## Для полностью автономной разработки в Cursor AI

---

## 📋 ОГЛАВЛЕНИЕ
1. [Контекст и цели проекта](#1-контекст-и-цели-проекта)
2. [Технический стек и архитектура](#2-технический-стек-и-архитектура)
3. [Структура проекта](#3-структура-проекта)
4. [Хронология разработки](#4-хронология-разработки)
5. [Промпты для каждого этапа](#5-промпты-для-каждого-этапа)
6. [API ключи и внешние сервисы](#6-api-ключи-и-внешние-сервисы)
7. [Тестирование и развертывание](#7-тестирование-и-развертывание)

---

## 1. КОНТЕКСТ И ЦЕЛИ ПРОЕКТА

### Что создаем
AI-ассистент в Telegram для агентов по недвижимости в России, который превращает хаотичную коммуникацию в структурированный календарь через обработку голосовых сообщений, текстов и скриншотов.

### Ключевые функции
- 🎤 **Голосовое управление**: "Запланируй показ трешки завтра в два"
- 📱 **Анализ скриншотов**: WhatsApp переписки, документы
- 🧠 **AI-автоматизация**: оптимизация маршрутов, напоминания
- 🏠 **Специализация**: понимание терминологии недвижимости

### Целевая аудитория
- Агенты жилой недвижимости (~150,000 человек)
- Агенты коммерческой недвижимости (~30,000 человек)  
- Ипотечные брокеры (~20,000 человек)

---

## 2. ТЕХНИЧЕСКИЙ СТЕК И АРХИТЕКТУРА

### Backend (оптимизированный стек)
```yaml
Language: Python 3.11+
Framework: FastAPI 0.104+
Database: PostgreSQL 15+ с pgvector для векторного поиска
Cache: Redis 7+
Queue: Celery + Redis
File Storage: LocalStorage (dev) / S3 (prod)
Container: Docker + Docker Compose
```

### AI/ML компоненты
```yaml
Speech Recognition: OpenAI Whisper (локально) + fallback на Yandex SpeechKit
NLP: OpenAI GPT-4 (основной) + Local LLM (backup)
OCR: EasyOCR + Tesseract (для документов)
Vector DB: pgvector в PostgreSQL
Embeddings: sentence-transformers (многоязычные)
```

### Архитектура (микросервисы)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │◄───│   API Gateway   │◄───│  Web Dashboard  │
│     Service     │    │    (FastAPI)    │    │   (Optional)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Service    │    │ Calendar Service│    │  User Service   │
│   (NLP/Voice)   │    │  (Events/Tasks) │    │ (Auth/Profile)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │  External APIs  │
│   + pgvector    │    │  (Cache/Queue)  │    │ (Maps/Speech)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 3. СТРУКТУРА ПРОЕКТА

### Файловая структура
```
realestate_bot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Настройки и переменные окружения
│   ├── database.py                # Database connection и sessions
│   │
│   ├── models/                    # SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── user.py               # Users, settings, preferences
│   │   ├── event.py              # Calendar events и tasks
│   │   ├── client.py             # Clients и contacts
│   │   ├── property.py           # Real estate objects
│   │   └── ai_data.py            # AI processing metadata
│   │
│   ├── schemas/                   # Pydantic схемы для API
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── client.py
│   │   ├── property.py
│   │   └── ai.py
│   │
│   ├── api/                       # FastAPI роуты
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Authentication
│   │   │   ├── users.py          # User management
│   │   │   ├── events.py         # Calendar operations
│   │   │   ├── clients.py        # Client management
│   │   │   ├── properties.py     # Property management
│   │   │   └── ai.py             # AI processing endpoints
│   │   └── deps.py               # Dependencies (auth, db)
│   │
│   ├── services/                  # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── user_service.py       # User operations
│   │   ├── calendar_service.py   # Calendar и event logic
│   │   ├── client_service.py     # Client management
│   │   ├── property_service.py   # Property operations
│   │   ├── ai_service.py         # AI coordination
│   │   ├── notification_service.py # Reminders и notifications
│   │   └── maps_service.py       # Route optimization
│   │
│   ├── ai/                        # AI/ML компоненты
│   │   ├── __init__.py
│   │   ├── speech/
│   │   │   ├── __init__.py
│   │   │   ├── whisper_client.py # Local Whisper
│   │   │   └── yandex_client.py  # Yandex SpeechKit fallback
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── openai_client.py  # OpenAI GPT integration
│   │   │   ├── local_llm.py      # Local LLM fallback
│   │   │   ├── real_estate_parser.py # Specialized NLP
│   │   │   └── intent_classifier.py  # Intent detection
│   │   ├── vision/
│   │   │   ├── __init__.py
│   │   │   ├── ocr_service.py    # OCR processing
│   │   │   └── image_classifier.py # Image type detection
│   │   └── embeddings/
│   │       ├── __init__.py
│   │       └── vector_service.py # Vector search
│   │
│   ├── bot/                       # Telegram Bot
│   │   ├── __init__.py
│   │   ├── main.py               # Bot entry point
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py          # /start, registration
│   │   │   ├── voice.py          # Voice message handler
│   │   │   ├── photo.py          # Photo/screenshot handler
│   │   │   ├── text.py           # Text message handler
│   │   │   ├── callback.py       # Inline keyboard callbacks
│   │   │   └── admin.py          # Admin commands
│   │   ├── keyboards/
│   │   │   ├── __init__.py
│   │   │   ├── inline.py         # Inline keyboards
│   │   │   └── reply.py          # Reply keyboards
│   │   ├── middlewares/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # User authentication
│   │   │   ├── throttle.py       # Rate limiting
│   │   │   └── logging.py        # Request logging
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── formatters.py     # Message formatting
│   │       └── validators.py     # Input validation
│   │
│   ├── core/                      # Утилиты и хелперы
│   │   ├── __init__.py
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── logging.py            # Logging configuration
│   │   ├── security.py           # Auth utilities
│   │   └── utils.py              # Common utilities
│   │
│   └── tasks/                     # Celery tasks
│       ├── __init__.py
│       ├── ai_tasks.py           # AI processing tasks
│       ├── notification_tasks.py # Notification sending
│       └── cleanup_tasks.py      # Cleanup и maintenance
│
├── migrations/                    # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/                         # Тесты
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   ├── test_ai/
│   └── test_bot/
│
├── scripts/                       # Utility scripts
│   ├── init_db.py                # Database initialization
│   ├── create_admin.py           # Create admin user
│   └── backup_db.py              # Database backup
│
├── docker/                        # Docker configuration
│   ├── Dockerfile.api
│   ├── Dockerfile.bot
│   ├── Dockerfile.celery
│   └── nginx.conf
│
├── docs/                          # Документация
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── .env.example                   # Environment variables template
├── .gitignore
├── docker-compose.yml             # Development environment
├── docker-compose.prod.yml        # Production environment
├── requirements.txt               # Python dependencies
├── alembic.ini                    # Alembic configuration
├── pyproject.toml                 # Project configuration
└── README.md
```

---

## 4. ХРОНОЛОГИЯ РАЗРАБОТКИ

### Этап 1: Базовая инфраструктура (1-2 дня)
```
1.1 Настройка проекта и зависимостей
1.2 Конфигурация базы данных PostgreSQL
1.3 Базовые модели SQLAlchemy
1.4 FastAPI application setup
1.5 Docker контейнеризация
```

### Этап 2: Telegram Bot основы (1 день)
```
2.1 Базовый Telegram bot handler
2.2 Middleware для аутентификации
2.3 Обработка команд /start, /help
2.4 Простые inline клавиатуры
```

### Этап 3: AI сервисы (2-3 дня)
```
3.1 OpenAI Whisper integration для speech-to-text
3.2 OpenAI GPT-4 для NLP processing
3.3 EasyOCR для обработки изображений
3.4 Специализированный парсер для недвижимости
3.5 Vector embeddings и поиск
```

### Этап 4: Календарь и события (1-2 дня)
```
4.1 Модели событий и календаря
4.2 CRUD операции для событий
4.3 Логика создания событий из текста/голоса
4.4 Система напоминаний
4.5 Оптимизация маршрутов
```

### Этап 5: Клиенты и недвижимость (1 день)
```
5.1 Модели клиентов и объектов
5.2 Парсинг контактной информации
5.3 Связывание событий с клиентами/объектами
5.4 Простая CRM функциональность
```

### Этап 6: Расширенная обработка (1-2 дня)
```
6.1 Обработка голосовых сообщений
6.2 Анализ скриншотов WhatsApp
6.3 OCR документов
6.4 Классификация типов контента
```

### Этап 7: Внешние интеграции (1 день)
```
7.1 Yandex Maps API для маршрутов
7.2 Геокодирование адресов
7.3 Расчет времени в пути
7.4 Fallback API сервисы
```

### Этап 8: Тестирование и оптимизация (1 день)
```
8.1 Unit тесты ключевых компонентов
8.2 Integration тесты API
8.3 Нагрузочное тестирование
8.4 Оптимизация производительности
```

### Этап 9: Production ready (1 день)
```
9.1 Production Docker setup
9.2 Environment configuration
9.3 Logging и monitoring
9.4 CI/CD pipeline
9.5 Deployment instructions
```

**Общее время разработки: 8-12 дней**

---

## 5. ПРОМПТЫ ДЛЯ КАЖДОГО ЭТАПА

### 5.1 Этап 1: Базовая инфраструктура

#### Промпт 1.1: Настройка проекта
```
Создай структуру проекта RealEstate Calendar Bot со следующими требованиями:

1. Создай структуру папок точно как показано в разделе "Структура проекта"
2. Настрой requirements.txt с версиями:
   - fastapi>=0.104.0
   - uvicorn[standard]>=0.24.0
   - sqlalchemy>=2.0.0
   - alembic>=1.12.0
   - asyncpg>=0.29.0
   - redis>=5.0.0
   - celery>=5.3.0
   - aiogram>=3.0.0
   - openai>=1.3.0
   - whisper>=1.1.10
   - easyocr>=1.7.0
   - sentence-transformers>=2.2.0
   - numpy>=1.24.0
   - pillow>=10.0.0
   - python-multipart>=0.0.6
   - python-jose[cryptography]>=3.3.0
   - passlib[bcrypt]>=1.7.4
   - aiofiles>=23.0.0
   - httpx>=0.25.0

3. Создай pyproject.toml с настройками для:
   - Black (форматирование кода)
   - isort (сортировка импортов)
   - mypy (type checking)
   - pytest (тестирование)

4. Создай .env.example со всеми необходимыми переменными окружения
5. Создай .gitignore для Python проекта
6. Создай базовый README.md с описанием проекта и инструкциями по запуску

Сделай это максимально профессионально, как для production проекта.
```

#### Промпт 1.2: Конфигурация и база данных
```
Создай следующие компоненты для работы с базой данных:

1. app/config.py - класс Settings с использованием pydantic BaseSettings для:
   - DATABASE_URL (PostgreSQL connection string)
   - REDIS_URL 
   - SECRET_KEY
   - TELEGRAM_BOT_TOKEN
   - OPENAI_API_KEY
   - YANDEX_SPEECHKIT_API_KEY
   - YANDEX_MAPS_API_KEY
   - Environment (dev/prod)
   - Logging settings

2. app/database.py - настройка SQLAlchemy 2.0 с:
   - Async engine
   - SessionLocal for dependency injection
   - Base class для моделей

3. alembic.ini - конфигурация Alembic для миграций

4. migrations/env.py - настройка Alembic с поддержкой async SQLAlchemy

5. Создай базовый docker-compose.yml для development с:
   - PostgreSQL 15 + pgvector extension
   - Redis 7
   - Adminer для работы с БД

Все должно работать "из коробки" после docker-compose up.
```

#### Промпт 1.3: Базовые модели SQLAlchemy
```
Создай SQLAlchemy модели в соответствующих файлах:

1. app/models/user.py - модель User с полями:
   - id (BigInteger, Primary Key)
   - telegram_id (BigInteger, Unique)
   - username, first_name, last_name (String, nullable)
   - phone (String, nullable)
   - timezone (String, default='Europe/Moscow')
   - settings (JSON, default={})
   - is_active (Boolean, default=True)
   - created_at, updated_at (DateTime with timezone)

2. app/models/event.py - модель Event с полями:
   - id (BigInteger, Primary Key)
   - user_id (ForeignKey to User)
   - title (String, не больше 500 символов)
   - description (Text, nullable)
   - start_time, end_time (DateTime with timezone)
   - location (String, nullable)
   - event_type (Enum: 'showing', 'meeting', 'deal', 'task')
   - status (Enum: 'active', 'completed', 'cancelled')
   - reminders (JSON array)
   - created_from (Enum: 'voice', 'text', 'image')
   - original_message (Text, nullable)
   - ai_confidence (Float, nullable)
   - created_at, updated_at (DateTime)

3. app/models/client.py - модель Client
4. app/models/property.py - модель Property  
5. app/models/ai_data.py - модель для хранения AI метаданных

Добавь все необходимые индексы для производительности.
Создай миграцию для создания всех таблиц.
```

### 5.2 Этап 2: Telegram Bot основы

#### Промпт 2.1: Базовый Telegram Bot
```
Создай базовую структуру Telegram бота с использованием aiogram 3.x:

1. app/bot/main.py - основной файл бота с:
   - Инициализация Bot и Dispatcher
   - Регистрация handlers и middlewares
   - Graceful shutdown

2. app/bot/handlers/start.py - обработчик команды /start:
   - Проверка регистрации пользователя в БД
   - Создание нового пользователя если не существует
   - Приветственное сообщение с inline клавиатурой
   - Краткая инструкция по использованию

3. app/bot/middlewares/auth.py - middleware для:
   - Автоматической регистрации пользователей
   - Проверки активности пользователя
   - Добавления user объекта в handler context

4. app/bot/keyboards/inline.py - inline клавиатуры:
   - Главное меню
   - Настройки
   - Помощь

5. Добавь базовую обработку ошибок и логирование

Используй async/await везде, следуй best practices aiogram 3.x.
```

### 5.3 Этап 3: AI сервисы

#### Промпт 3.1: Speech Recognition сервис
```
Создай сервис для обработки голосовых сообщений:

1. app/ai/speech/whisper_client.py - класс WhisperClient:
   - Использует OpenAI Whisper для локального распознавания
   - Метод transcribe_audio(audio_file_path: str) -> str
   - Поддержка русского языка
   - Обработка ошибок и fallback

2. app/ai/speech/yandex_client.py - класс YandexSpeechClient:
   - Fallback для Whisper через Yandex SpeechKit API
   - Async методы для API calls
   - Retry logic с exponential backoff

3. app/ai/speech/__init__.py - фасад SpeechRecognitionService:
   - Автоматический выбор между Whisper и Yandex
   - Кэширование результатов в Redis
   - Метрики производительности

4. app/services/ai_service.py - интеграция с основной логикой:
   - Метод process_voice_message()
   - Сохранение результатов в БД
   - Интеграция с NLP обработкой

Добавь comprehensive error handling и логирование.
Сделай чтобы можно было легко переключать между провайдерами.
```

#### Промпт 3.2: NLP обработка
```
Создай систему NLP обработки специализированную для недвижимости:

1. app/ai/nlp/real_estate_parser.py - класс RealEstateNLPProcessor:
   - Извлечение сущностей: адреса, клиенты, время, типы недвижимости
   - Классификация интентов: показ, встреча, сделка, задача
   - Парсинг русских дат и времени ("завтра в два", "через час")
   - Нормализация адресов ("Пушкина 15" -> полный адрес)

2. app/ai/nlp/intent_classifier.py - классификация намерений:
   - Определение типа события по тексту
   - Уверенность в классификации
   - Поддержка неформальной речи агентов

3. app/ai/nlp/openai_client.py - интеграция с OpenAI:
   - Structured output с Pydantic моделями
   - Специальные промпты для недвижимости
   - Retry logic и rate limiting

4. Создай Pydantic схемы для:
   - ParsedEvent (извлеченная информация о событии)
   - ExtractedEntities (адреса, имена, телефоны, время)
   - ClassificationResult (тип события, уверенность)

Включи специальные паттерны для:
- Типов недвижимости (двушка, трешка, студия, офис)
- Сделок (показ, продажа, аренда, ипотека)
- Русских адресов и районов
```

### 5.4 Этап 4: Календарь и события

#### Промпт 4.1: Calendar Service
```
Создай сервис для работы с календарем и событиями:

1. app/services/calendar_service.py - класс CalendarService:
   - create_event_from_text() - создание события из текста/голоса
   - create_event_from_image() - создание из скриншота
   - get_user_schedule() - получение расписания пользователя
   - optimize_schedule() - оптимизация маршрутов
   - check_conflicts() - проверка пересечений событий
   - send_reminders() - отправка напоминаний

2. app/services/notification_service.py - система напоминаний:
   - Celery tasks для отложенных напоминаний
   - Персонализированные напоминания по типу события
   - Напоминания с чек-листами для агентов

3. app/api/v1/events.py - REST API endpoints:
   - GET /events - список событий пользователя
   - POST /events - создание события
   - PUT /events/{id} - редактирование
   - DELETE /events/{id} - удаление
   - POST /events/optimize - оптимизация расписания

4. app/schemas/event.py - Pydantic схемы:
   - EventCreate, EventUpdate, EventResponse
   - ScheduleOptimization request/response
   - ReminderSettings

Добавь валидацию:
- Проверка временных промежутков
- Проверка форматов адресов
- Ограничения на количество событий в день
```

### 5.5 Этап 5: Обработка голоса и изображений

#### Промпт 5.1: Voice Message Handler
```
Создай полную обработку голосовых сообщений в Telegram боте:

1. app/bot/handlers/voice.py:
   - Обработчик voice messages от Telegram
   - Скачивание и конвертация аудио
   - Интеграция с SpeechRecognitionService
   - Показ прогресса обработки пользователю
   - Интерактивное подтверждение создания события

2. Workflow обработки голоса:
   - Скачать аудио файл
   - Конвертировать в нужный формат (если нужно)
   - Отправить в speech-to-text
   - Обработать текст через NLP
   - Показать пользователю извлеченную информацию
   - Дать возможность подтвердить/исправить
   - Создать событие в календаре

3. Интерактивные элементы:
   - Inline кнопки для подтверждения
   - Возможность редактировать поля
   - Кнопки "Создать", "Исправить", "Отменить"

4. Error handling:
   - Слишком длинное аудио
   - Неразборчивая речь
   - Ошибки распознавания
   - Fallback на ручной ввод

Сделай UX максимально простым - агент говорит, бот понимает и создает событие.
```

#### Промпт 5.2: Image/Screenshot Handler
```
Создай систему обработки изображений и скриншотов:

1. app/bot/handlers/photo.py:
   - Обработка изображений от пользователя
   - Классификация типа изображения
   - Специальная обработка WhatsApp скриншотов
   - OCR обработка документов

2. app/ai/vision/image_classifier.py:
   - Определение типа изображения:
     - WhatsApp переписка
     - Объявление о недвижимости
     - Документ (договор, выписка ЕГРН)
     - Календарь/расписание
     - Рукописные заметки

3. app/ai/vision/ocr_service.py:
   - EasyOCR для извлечения текста
   - Постобработка текста (исправление ошибок)
   - Извлечение структурированных данных
   - Специальная обработка русского текста

4. Специальные обработчики:
   - WhatsApp: извлечение имен, телефонов, адресов, времени
   - Документы: извлечение реквизитов, дат, сумм
   - Объявления: цена, площадь, адрес, характеристики

Добавь валидацию качества изображений и понятные ошибки для пользователя.
```

### 5.6 Этап 6: External APIs

#### Промпт 6.1: Yandex Maps Integration
```
Создай интеграцию с Yandex Maps для геолокации и маршрутов:

1. app/services/maps_service.py - класс YandexMapsService:
   - geocode_address() - получение координат по адресу
   - reverse_geocode() - адрес по координатам
   - calculate_route() - расчет маршрута между точками
   - calculate_travel_time() - время в пути
   - optimize_route() - оптимизация маршрута для нескольких точек

2. Оптимизация расписания:
   - Анализ всех событий дня пользователя
   - Расчет оптимального порядка посещений
   - Учет времени в пути между локациями
   - Предложения по изменению времени встреч

3. app/services/route_optimizer.py:
   - Алгоритм оптимизации маршрута (TSP solver)
   - Учет приоритетов событий
   - Буферное время между встречами
   - Интеграция с календарем

4. Кэширование и производительность:
   - Кэш геокодирования в Redis
   - Batch обработка запросов
   - Retry logic для API calls

Добавь fallback на OpenStreetMap если Yandex недоступен.
```

### 5.7 Этап 7: Production Готовность

#### Промпт 7.1: Docker и Development Setup
```
Создай production-ready Docker конфигурацию:

1. docker/Dockerfile.api - для FastAPI сервиса:
   - Multi-stage build для оптимизации размера
   - Non-root user для безопасности
   - Health checks
   - Proper signal handling

2. docker/Dockerfile.bot - для Telegram бота:
   - Отдельный контейнер для бота
   - Graceful shutdown handling
   - Restart policies

3. docker/Dockerfile.celery - для background tasks:
   - Celery worker и beat scheduler
   - Monitoring и health checks

4. docker-compose.yml - development environment:
   - All services with proper networking
   - Volume mounts для development
   - Environment variables
   - Database initialization

5. docker-compose.prod.yml - production environment:
   - Production-optimized settings
   - Secrets management
   - Resource limits
   - Logging configuration

Добавь nginx reverse proxy и SSL termination.
```

#### Промпт 7.2: Testing и CI/CD
```
Создай comprehensive testing suite:

1. tests/conftest.py - pytest configuration:
   - Database fixtures с test database
   - Mock external APIs (OpenAI, Yandex)
   - Test client для FastAPI
   - Cleanup после тестов

2. tests/test_api/ - API endpoint тесты:
   - Все CRUD операции
   - Authentication и authorization
   - Error handling
   - Input validation

3. tests/test_services/ - бизнес-логика тесты:
   - CalendarService unit tests
   - AI Service mocking
   - Maps service integration tests

4. tests/test_ai/ - AI компоненты тесты:
   - NLP processing с sample data
   - Speech recognition mocking
   - OCR тесты с sample images

5. .github/workflows/ci.yml - GitHub Actions:
   - Run tests on PR
   - Code quality checks (black, isort, mypy)
   - Docker image building
   - Security scanning

Добавь coverage reporting и интеграцию с codecov.
```

---

## 6. API КЛЮЧИ И ВНЕШНИЕ СЕРВИСЫ

### Необходимые API ключи и настройка

#### 6.1 Telegram Bot Token
```bash
# Создание бота
1. Написать @BotFather в Telegram
2. Команда /newbot
3. Выбрать имя: RealEstate Calendar Bot
4. Выбрать username: реalestate_calendar_bot
5. Получить токен: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Добавить в .env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### 6.2 OpenAI API Key
```bash
# Получение ключа
1. Зайти на https://platform.openai.com
2. Создать аккаунт и войти
3. API Keys -> Create new secret key
4. Скопировать ключ: sk-...

# Добавить в .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

#### 6.3 Yandex Cloud APIs
```bash
# Yandex SpeechKit
1. console.cloud.yandex.ru
2. Создать сервисный аккаунт
3. Назначить роль: ai.speechkit.user
4. Создать API ключ
YANDEX_SPEECHKIT_API_KEY=AQVN...

# Yandex Maps
1. developer.tech.yandex.ru
2. Получить ключ для Geocoder API
YANDEX_MAPS_API_KEY=12345678-1234-1234-1234-123456789012
```

#### 6.4 Автоматическая настройка сервисов
```python
# scripts/setup_external_apis.py
"""
Скрипт для проверки и настройки всех внешних API.
Запускается автоматически при первом старте приложения.
"""

async def check_api_keys():
    """Проверить все API ключи и вывести инструкции для отсутствующих"""
    
    checks = {
        "Telegram Bot": check_telegram_bot_token(),
        "OpenAI": check_openai_api_key(),
        "Yandex SpeechKit": check_yandex_speechkit(),
        "Yandex Maps": check_yandex_maps()
    }
    
    for service, result in checks.items():
        if result:
            logger.info(f"✅ {service} - OK")
        else:
            logger.error(f"❌ {service} - требует настройки")
            print_setup_instructions(service)
```

---

## 7. ТЕСТИРОВАНИЕ И РАЗВЕРТЫВАНИЕ

### 7.1 Стратегия тестирования

#### Unit тесты
```python
# Тестирование AI сервисов
def test_real_estate_nlp_parser():
    """Тест парсинга голосовых команд недвижимости"""
    
def test_speech_recognition_fallback():
    """Тест fallback между Whisper и Yandex"""
    
def test_calendar_conflict_detection():
    """Тест обнаружения конфликтов в расписании"""
```

#### Integration тесты  
```python
# Тестирование полного workflow
def test_voice_to_calendar_workflow():
    """Тест: голос -> текст -> событие -> календарь"""
    
def test_whatsapp_screenshot_processing():
    """Тест обработки скриншота WhatsApp"""
```

### 7.2 Deployment

#### Локальный запуск (Development)
```bash
# 1. Клонирование и настройка
git clone <repo>
cd realestate_bot
cp .env.example .env
# Заполнить .env файл

# 2. Запуск через Docker
docker-compose up -d

# 3. Инициализация БД
docker-compose exec api python scripts/init_db.py

# 4. Создание админа
docker-compose exec api python scripts/create_admin.py

# 5. Запуск тестов
docker-compose exec api pytest
```

#### Production deployment
```bash
# 1. Сервер подготовка
apt update && apt install docker.io docker-compose-plugin

# 2. Environment setup
cp .env.example .env.prod
# Заполнить production настройки

# 3. Production запуск
docker-compose -f docker-compose.prod.yml up -d

# 4. SSL настройка (Let's Encrypt)
certbot --nginx -d yourdomain.com

# 5. Monitoring
docker-compose logs -f
```

---

## 8. ФИНАЛЬНЫЕ ИНСТРУКЦИИ ДЛЯ CURSOR AI

### Порядок выполнения промптов

1. **СТРОГО следуй хронологии** - не переходи к следующему этапу пока не завершен предыдущий
2. **Используй указанные промпты** - копируй их точно как написано
3. **Создавай все файлы** - не пропускай ничего из структуры проекта
4. **Тестируй каждый этап** - убеждайся что код работает перед переходом дальше
5. **Запрашивай API ключи** только когда дойдешь до соответствующего этапа

### Работа с контекстом

- **Всегда** ссылайся на это ТЗ при любых вопросах
- **Помни** специфику проекта - это бот для агентов недвижимости
- **Учитывай** русский язык и российскую специфику
- **Сохраняй** архитектурные решения между этапами

### Когда запрашивать помощь

1. **API ключи** - когда дойдешь до интеграции конкретного сервиса
2. **Настройки production** - при настройке deployment
3. **Неясности в требованиях** - если что-то в ТЗ неочевидно

### Финальный результат

После выполнения всех этапов должен получиться полностью рабочий RealEstate Calendar Bot который:

✅ Обрабатывает голосовые сообщения на русском языке  
✅ Создает события в календаре из неформальной речи  
✅ Анализирует скриншоты WhatsApp  
✅ Оптимизирует маршруты агентов  
✅ Работает в production с Docker  
✅ Имеет comprehensive тесты  
✅ Готов к масштабированию  

**НАЧИНАЙ РАЗРАБОТКУ С ЭТАПА 1.1!** 