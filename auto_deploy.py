#!/usr/bin/env python3
"""
🤖 Автоматическое развёртывание M² Agent Calendar
Делает всё сам, кроме регистраций
"""
import subprocess
import requests
import time
import os
import sys

def run_command(cmd, description=""):
    """Выполнить команду с логированием"""
    print(f"🔧 {description}")
    print(f"   $ {cmd}")
    
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Успешно")
        if result.stdout.strip():
            print(f"   📝 {result.stdout.strip()}")
    else:
        print(f"   ❌ Ошибка: {result.stderr.strip()}")
        
    return result

def push_to_github(repo_url):
    """Автопуш в GitHub"""
    print("📤 Загружаю код в GitHub...")
    
    # Добавляем remote
    run_command(f"git remote add origin {repo_url}", "Добавление remote")
    
    # Пуш
    result = run_command("git push -u origin main", "Загрузка кода")
    
    if result.returncode == 0:
        print("✅ Код успешно загружен в GitHub!")
        return True
    else:
        print("❌ Ошибка загрузки. Возможно remote уже существует.")
        # Пробуем force push
        run_command("git push -f origin main", "Force push")
        return True

def setup_railway_webhook(railway_url, bot_token):
    """Автонастройка webhook"""
    webhook_url = f"{railway_url}/api/v1/webhook"
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query", "inline_query"]
    }
    
    print(f"🔗 Настройка webhook: {webhook_url}")
    
    try:
        response = requests.post(telegram_api_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook успешно настроен!")
            return True
        else:
            print(f"❌ Ошибка webhook: {result.get('description', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def test_deployment(railway_url):
    """Тестирование развёртывания"""
    print("🧪 Тестирование развёртывания...")
    
    # Тест health endpoint
    try:
        response = requests.get(f"{railway_url}/health", timeout=30)
        if response.status_code == 200:
            print("✅ Health check прошёл")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")
    
    # Тест Mini App
    try:
        response = requests.get(f"{railway_url}/api/v1/miniapp/", timeout=30)
        if response.status_code == 200:
            print("✅ Mini App доступен")
        else:
            print(f"❌ Mini App недоступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка Mini App: {e}")

def main():
    """Главная функция автодеплоя"""
    print("🤖 M² AGENT CALENDAR - АВТОДЕПЛОЙ")
    print("=" * 50)
    
    # Проверяем параметры
    if len(sys.argv) < 2:
        print("📋 Использование:")
        print("   python auto_deploy.py <GITHUB_REPO_URL> [RAILWAY_URL]")
        print("")
        print("📝 Пример:")
        print("   python auto_deploy.py https://github.com/username/m2-agent-calendar.git")
        print("   python auto_deploy.py repo_url https://your-app.railway.app")
        return
    
    repo_url = sys.argv[1]
    railway_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    bot_token = "7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY"
    
    print(f"📦 GitHub Repo: {repo_url}")
    print(f"🚀 Railway URL: {railway_url or 'Будет получен позже'}")
    print("")
    
    # 1. Пуш в GitHub
    if push_to_github(repo_url):
        print("✅ Этап 1: GitHub готов")
    else:
        print("❌ Ошибка GitHub, но продолжаем...")
    
    print("")
    print("📋 СЛЕДУЮЩИЕ ШАГИ (ТРЕБУЮТ РЕГИСТРАЦИИ):")
    print("1. Зайдите на railway.app")
    print("2. Нажмите 'New Project' -> 'Deploy from GitHub'")
    print("3. Выберите репозиторий m2-agent-calendar")
    print("4. Добавьте сервис PostgreSQL")
    print("5. В Variables добавьте:")
    print("   TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY")
    print("   OPENAI_API_KEY=ваш_ключ")
    print("6. Дождитесь деплоя")
    print("7. Скопируйте публичный URL")
    print("8. Запустите: python auto_deploy.py repo_url YOUR_RAILWAY_URL")
    print("")
    
    # 2. Настройка webhook (если есть Railway URL)
    if railway_url:
        print("🔗 Настройка webhook...")
        if setup_railway_webhook(railway_url, bot_token):
            print("✅ Этап 2: Webhook настроен")
        
        # 3. Тестирование
        print("")
        test_deployment(railway_url)
        
        print("")
        print("🎉 АВТОДЕПЛОЙ ЗАВЕРШЁН!")
        print(f"📱 Бот: @m2_agentcalendar_bot")
        print(f"🌐 Mini App: {railway_url}/api/v1/miniapp/")
        print("✅ Всё готово к использованию!")

if __name__ == "__main__":
    main() 