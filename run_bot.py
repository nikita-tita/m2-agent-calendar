#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота с проверками
"""

import os
import sys
import asyncio
from pathlib import Path

def check_requirements():
    """Проверяем наличие всех требований"""
    print("🔍 Проверяю настройки...")
    
    # Проверяем переменные окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("💡 Установите переменную окружения:")
        print("   export TELEGRAM_BOT_TOKEN='ваш-токен-от-botfather'")
        return False
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "YOUR_OPENAI_API_KEY_HERE":
        print("⚠️  OPENAI_API_KEY не установлен (AI-функции будут ограничены)")
        print("💡 Для полной функциональности:")
        print("   export OPENAI_API_KEY='sk-ваш-ключ-openai'")
    
    # Проверяем виртуальное окружение
    if not hasattr(sys, 'real_prefix') and not hasattr(sys, 'base_prefix'):
        venv_path = Path("venv")
        if venv_path.exists():
            print("⚠️  Виртуальное окружение не активировано")
            print("💡 Активируйте командой: source venv/bin/activate")
        else:
            print("❌ Виртуальное окружение не найдено!")
            print("💡 Создайте командой: python -m venv venv")
            return False
    
    print("✅ Проверки пройдены!")
    return True

def main():
    """Главная функция"""
    print("🤖 Запуск Telegram-бота для агентов недвижимости")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Не все требования выполнены. Исправьте ошибки и попробуйте снова.")
        sys.exit(1)
    
    print("\n🚀 Запускаю бота...")
    print("📝 Логи будут отображаться ниже:")
    print("-" * 50)
    
    try:
        # Импортируем и запускаем бота
        from app.bot.main import main as bot_main
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Бот остановлен пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка запуска: {e}")
        print("🔧 Проверьте логи выше для диагностики")
        sys.exit(1)

if __name__ == "__main__":
    main() 