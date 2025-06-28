#!/bin/bash

# 🚀 M² Agent Calendar - Быстрый старт
# Запускает всю систему за 30 секунд

echo "🚀 M² AGENT CALENDAR - БЫСТРЫЙ СТАРТ"
echo "=" * 50

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker Desktop"
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

echo "✅ Docker готов"

# Остановка существующих контейнеров
echo "🛑 Останавливаю существующие контейнеры..."
docker-compose -f docker-compose.cloud.yml down 2>/dev/null || true

# Сборка и запуск
echo "🏗️ Собираю и запускаю систему..."
docker-compose -f docker-compose.cloud.yml up --build -d

# Ожидание запуска
echo "⏳ Жду запуска системы..."
sleep 30

# Применение миграций
echo "🗄️ Применяю миграции базы данных..."
docker-compose -f docker-compose.cloud.yml exec app alembic upgrade head

# Проверка статуса
echo "🧪 Проверяю статус системы..."

# Health check
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API работает: http://localhost:8000"
else
    echo "❌ API недоступен"
fi

# Mini App check
if curl -s http://localhost:8000/api/v1/miniapp/ | grep -q "DOCTYPE"; then
    echo "✅ Mini App работает: http://localhost:8000/api/v1/miniapp/"
else
    echo "❌ Mini App недоступен"
fi

# Логи
echo ""
echo "📊 СТАТУС СИСТЕМЫ:"
docker-compose -f docker-compose.cloud.yml ps

echo ""
echo "🎉 СИСТЕМА ЗАПУЩЕНА!"
echo "📱 Telegram Bot: @m2_agentcalendar_bot" 
echo "🌐 API: http://localhost:8000"
echo "📅 Mini App: http://localhost:8000/api/v1/miniapp/"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "1. Откройте ngrok для публичного доступа:"
echo "   ngrok http 8000"
echo "2. Настройте webhook с публичным URL"
echo "3. Протестируйте бота в Telegram"

# Логи в реальном времени
echo ""
echo "📝 Логи системы (Ctrl+C для выхода):"
docker-compose -f docker-compose.cloud.yml logs -f 