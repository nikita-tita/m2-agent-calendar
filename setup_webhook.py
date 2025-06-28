#!/usr/bin/env python3
"""
Скрипт для настройки Telegram webhook после деплоя на Railway
"""
import requests
import os
import sys

def setup_webhook(railway_url: str, bot_token: str):
    """Настройка webhook для Telegram бота"""
    
    webhook_url = f"{railway_url}/api/v1/webhook"
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"]
    }
    
    print(f"🔗 Настройка webhook:")
    print(f"   Бот: {bot_token[:10]}...")
    print(f"   URL: {webhook_url}")
    print("")
    
    try:
        response = requests.post(telegram_api_url, json=payload)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook успешно настроен!")
            print(f"   Описание: {result.get('description', 'N/A')}")
        else:
            print("❌ Ошибка настройки webhook:")
            print(f"   {result.get('description', 'Неизвестная ошибка')}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def main():
    """Главная функция"""
    
    if len(sys.argv) != 3:
        print("📋 Использование:")
        print("   python setup_webhook.py <RAILWAY_URL> <BOT_TOKEN>")
        print("")
        print("📝 Пример:")
        print("   python setup_webhook.py https://your-app.railway.app 7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY")
        return
    
    railway_url = sys.argv[1].rstrip('/')
    bot_token = sys.argv[2]
    
    print("🚀 Настройка M² Agent Calendar Bot")
    print("=" * 40)
    
    setup_webhook(railway_url, bot_token)

if __name__ == "__main__":
    main() 