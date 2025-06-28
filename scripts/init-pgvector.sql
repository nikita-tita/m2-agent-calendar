-- Инициализация расширения pgvector для векторного поиска
CREATE EXTENSION IF NOT EXISTS vector;

-- Создание базы данных если не существует
-- (PostgreSQL создает БД автоматически через переменные окружения)

-- Проверка что расширение установлено
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create basic database setup
-- Note: Table-specific indexes will be created by Alembic migrations 