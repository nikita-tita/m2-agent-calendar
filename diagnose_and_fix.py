#!/usr/bin/env python3
"""
🔧 M² Agent Calendar - Диагностика и исправление
Автоматическая проверка и исправление проблем системы
"""

import os
import sys
import requests
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔧 {text}")
    print(f"{'='*60}")

def print_step(step, text):
    print(f"\n{step}. {text}")
    print("-" * 40)

def check_env_file():
    """Проверка файла .env"""
    print_step("1", "Проверка переменных окружения")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден")
        
        # Создаём .env файл
        env_content = """# M² Agent Calendar - Environment Variables
TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY
OPENAI_API_KEY=your_openai_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/m2_calendar

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=production
DEBUG=False
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Создан файл .env с базовыми настройками")
        print("⚠️  ВАЖНО: Добавьте ваш OPENAI_API_KEY в файл .env")
    else:
        print("✅ Файл .env существует")

def check_main_app():
    """Проверка основного приложения"""
    print_step("2", "Проверка app/main.py")
    
    main_path = Path("app/main.py")
    if main_path.exists():
        print("✅ app/main.py найден")
        
        # Проверяем содержимое
        content = main_path.read_text()
        if "FastAPI" in content and "/webhook" in content:
            print("✅ FastAPI приложение настроено корректно")
        else:
            print("⚠️  Возможны проблемы в app/main.py")
    else:
        print("❌ app/main.py не найден!")

def check_requirements():
    """Проверка requirements.txt"""
    print_step("3", "Проверка requirements.txt")
    
    req_path = Path("requirements.txt")
    if req_path.exists():
        print("✅ requirements.txt найден")
        
        content = req_path.read_text()
        required_packages = ["fastapi", "uvicorn", "sqlalchemy", "aiogram"]
        missing = []
        
        for pkg in required_packages:
            if pkg.lower() not in content.lower():
                missing.append(pkg)
        
        if missing:
            print(f"⚠️  Отсутствующие пакеты: {', '.join(missing)}")
        else:
            print("✅ Все основные пакеты включены")
    else:
        print("❌ requirements.txt не найден!")

def test_webhook_endpoint(url):
    """Тестирование webhook endpoint"""
    print_step("4", f"Тестирование webhook: {url}")
    
    webhook_url = f"{url}/api/v1/webhook"
    health_url = f"{url}/health"
    
    try:
        # Проверка health endpoint
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Health check: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
        # Проверка webhook endpoint
        test_data = {"message": {"text": "/start", "from": {"id": 123}}}
        response = requests.post(webhook_url, json=test_data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Webhook работает: {response.json()}")
            return True
        else:
            print(f"❌ Webhook не работает: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def setup_webhook(app_url):
    """Настройка Telegram webhook"""
    print_step("5", "Настройка Telegram webhook")
    
    bot_token = "7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY"
    webhook_url = f"{app_url}/api/v1/webhook"
    
    try:
        # Устанавливаем webhook
        telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        response = requests.post(telegram_url, json={"url": webhook_url})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print(f"✅ Webhook установлен: {webhook_url}")
                return True
            else:
                print(f"❌ Ошибка Telegram API: {result}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return False

def main():
    print_header("ДИАГНОСТИКА M² AGENT CALENDAR")
    
    # Основные проверки
    check_env_file()
    check_main_app()
    check_requirements()
    
    # Запрос URL приложения
    print_step("4", "Введите URL вашего развёрнутого приложения")
    print("Примеры:")
    print("- Render: https://m2-agent-calendar.onrender.com")
    print("- Railway: https://your-app.railway.app")
    print("- Heroku: https://your-app.herokuapp.com")
    
    app_url = input("\n🔗 URL приложения: ").strip()
    
    if not app_url:
        print("❌ URL не указан!")
        return
    
    if not app_url.startswith("http"):
        app_url = f"https://{app_url}"
    
    # Тестирование
    if test_webhook_endpoint(app_url):
        if setup_webhook(app_url):
            print_header("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
            print(f"✅ Приложение: {app_url}")
            print(f"✅ Webhook: {app_url}/api/v1/webhook")
            print(f"✅ Telegram bot: @m2_agentcalendar_bot")
            print("\n📱 Теперь проверьте бота в Telegram командой /start")
        else:
            print_header("⚠️  WEBHOOK НЕ НАСТРОЕН")
            print("Приложение работает, но webhook не установлен")
    else:
        print_header("❌ ПРОБЛЕМЫ С ПРИЛОЖЕНИЕМ")
        print("Приложение не отвечает или работает некорректно")
        print("\n🔧 Рекомендации:")
        print("1. Проверьте логи в панели управления хостинга")
        print("2. Убедитесь, что установлены переменные окружения")
        print("3. Проверьте Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT")

if __name__ == "__main__":
    main() 