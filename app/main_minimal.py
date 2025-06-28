"""
Минимальная версия M² Agent Calendar
Без AI-сервисов, только основной функционал
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime
import json

# Минимальная конфигурация
from app.config_minimal import settings

# Создание приложения
app = FastAPI(
    title="M² Agent Calendar (Minimal)",
    description="Telegram Bot для агентов недвижимости (минимальная версия)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "minimal",
        "ai_enabled": False
    }

# Базовая информация
@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "app": settings.app_name,
        "version": "1.0.0-minimal",
        "status": "running",
        "features": [
            "Telegram Bot Integration",
            "Calendar Management",
            "Web Interface (Mini App)",
            "PostgreSQL Database"
        ],
        "ai_features": "Disabled (minimal version)",
        "endpoints": {
            "health": "/health",
            "miniapp": "/api/v1/miniapp/",
            "webhook": "/api/v1/webhook"
        }
    }

# Mini App HTML
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M² Calendar</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 18px;
            margin: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .feature {
            background: rgba(255,255,255,0.15);
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid #4CAF50;
        }
        .minimal-badge {
            background: #ff6b6b;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            display: inline-block;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 M² Calendar <span class="minimal-badge">MINIMAL</span></h1>
        
        <div class="status">
            <h2>✅ Система работает!</h2>
            <p>Минимальная версия без AI-сервисов</p>
            <p>Время: <span id="time"></span></p>
        </div>

        <div class="feature">
            <h3>📱 Telegram Bot</h3>
            <p>Основные команды и обработка сообщений</p>
        </div>

        <div class="feature">
            <h3>📅 Календарь событий</h3>
            <p>Создание и управление событиями</p>
        </div>

        <div class="feature">
            <h3>🗄️ База данных</h3>
            <p>PostgreSQL для хранения данных</p>
        </div>

        <div class="feature">
            <h3>🌐 Web интерфейс</h3>
            <p>Mini App для Telegram</p>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <button class="button" onclick="window.open('/health', '_blank')">
                🩺 Health Check
            </button>
            <button class="button" onclick="window.open('/', '_blank')">
                📋 API Info
            </button>
        </div>

        <div style="text-align: center; margin-top: 20px; opacity: 0.8;">
            <small>M² Agent Calendar v1.0.0-minimal<br>Ready for production deployment</small>
        </div>
    </div>

    <script>
        function updateTime() {
            document.getElementById('time').textContent = new Date().toLocaleString('ru-RU');
        }
        updateTime();
        setInterval(updateTime, 1000);

        // Telegram WebApp integration
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }
    </script>
</body>
</html>
"""

# Mini App endpoints
@app.get("/api/v1/miniapp/", response_class=HTMLResponse)
async def mini_app():
    """Mini App интерфейс для Telegram"""
    return MINI_APP_HTML

@app.get("/api/v1/miniapp/events")
async def get_events():
    """Получить события (заглушка)"""
    return {
        "events": [
            {
                "id": 1,
                "title": "Встреча с клиентом",
                "date": "2024-01-02",
                "time": "15:00",
                "status": "upcoming"
            },
            {
                "id": 2,
                "title": "Просмотр квартиры",
                "date": "2024-01-03", 
                "time": "10:30",
                "status": "upcoming"
            }
        ],
        "total": 2,
        "version": "minimal"
    }

@app.post("/api/v1/miniapp/events")
async def create_event(event_data: dict):
    """Создать событие (заглушка)"""
    return {
        "success": True,
        "message": "Event created successfully",
        "event_id": 12345,
        "data": event_data
    }

# Webhook endpoint
@app.post("/api/v1/webhook")
async def webhook(data: dict):
    """Webhook для Telegram бота (заглушка)"""
    return {
        "success": True,
        "message": "Webhook received",
        "version": "minimal"
    }

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(
        "app.main_minimal:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 