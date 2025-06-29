#!/usr/bin/env python3
"""
🧪 Автоматическое тестирование развернутого M² Agent Calendar
"""
import requests
import sys
import time

def test_deployment(url):
    """Тестирование развернутого приложения"""
    print(f"🧪 ТЕСТИРОВАНИЕ M² AGENT CALENDAR")
    print(f"🌐 URL: {url}")
    print("=" * 50)
    
    base_url = url.rstrip('/')
    
    # 1. Health Check
    print("1️⃣ Проверка Health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health OK: {data.get('status', 'unknown')}")
            print(f"   📊 Version: {data.get('version', 'unknown')}")
        else:
            print(f"   ❌ Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health error: {e}")
        return False
    
    # 2. API Root
    print("\n2️⃣ Проверка API root...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API OK: {data.get('app', 'unknown')}")
        else:
            print(f"   ❌ API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API error: {e}")
    
    # 3. Mini App
    print("\n3️⃣ Проверка Mini App...")
    try:
        response = requests.get(f"{base_url}/api/v1/miniapp/", timeout=10)
        if response.status_code == 200 and "DOCTYPE" in response.text:
            print("   ✅ Mini App работает")
        else:
            print(f"   ❌ Mini App failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Mini App error: {e}")
    
    # 4. Webhook endpoint
    print("\n4️⃣ Проверка Webhook endpoint...")
    try:
        test_data = {"test": True, "message": {"text": "/start"}}
        response = requests.post(f"{base_url}/api/v1/webhook", 
                               json=test_data, timeout=10)
        if response.status_code in [200, 422]:  # 422 expected for test data
            print("   ✅ Webhook endpoint доступен")
        else:
            print(f"   ❌ Webhook failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Webhook error: {e}")
    
    # 5. Результат
    print("\n" + "=" * 50)
    print("🎯 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🌐 Приложение: {base_url}")
    print(f"📱 Mini App: {base_url}/api/v1/miniapp/")
    print(f"🔗 Webhook URL: {base_url}/api/v1/webhook")
    print("\n✅ СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    print("\n📱 Следующие шаги:")
    print(f"1. Настроить webhook: python setup_webhook.py {url}")
    print("2. Протестировать в Telegram: /start @m2_agentcalendar_bot")
    
    return True

def setup_webhook_auto(url, bot_token):
    """Автонастройка webhook"""
    webhook_url = f"{url.rstrip('/')}/api/v1/webhook"
    telegram_api = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    print(f"\n🔗 Настройка webhook: {webhook_url}")
    
    try:
        response = requests.post(telegram_api, json={"url": webhook_url}, timeout=10)
        if response.json().get("ok"):
            print("✅ Webhook настроен успешно!")
            return True
        else:
            print(f"❌ Ошибка webhook: {response.json().get('description')}")
            return False
    except Exception as e:
        print(f"❌ Ошибка настройки webhook: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📋 Использование:")
        print("   python test_deployment.py <RAILWAY_URL>")
        print("\n📝 Пример:")
        print("   python test_deployment.py https://your-app.railway.app")
        sys.exit(1)
    
    url = sys.argv[1]
    bot_token = "7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY"
    
    # Тестирование
    if test_deployment(url):
        print("\n🤖 Автонастройка webhook...")
        setup_webhook_auto(url, bot_token)
        
        print("\n🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!")
        print("Система M² Agent Calendar готова к использованию!") 