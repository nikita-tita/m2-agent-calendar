#!/usr/bin/env python3
"""
🔧 Railway Config Fix - Патч для использования SQLite если нет PostgreSQL
"""
import os
import sys
from pathlib import Path

def fix_database_config():
    """Исправляет конфигурацию БД для Railway"""
    
    # Создаём environment variable для Railway с SQLite
    railway_env = """
# Railway Environment Fix - SQLite fallback
DATABASE_URL=sqlite+aiosqlite:///./railway_db.sqlite
ENVIRONMENT=production
DEBUG=False
"""
    
    # Создаём директорию для БД
    db_dir = Path("./db")
    db_dir.mkdir(exist_ok=True)
    
    # Обновляем .env файл
    env_path = Path(".env")
    current_env = ""
    if env_path.exists():
        current_env = env_path.read_text()
    
    # Добавляем Railway конфигурацию
    if "# Railway Environment Fix" not in current_env:
        with open(".env", "a") as f:
            f.write(railway_env)
        print("✅ Добавлена SQLite конфигурация в .env")
    
    # Создаём railway.env для деплоя
    with open("railway.env", "w") as f:
        f.write("""# Railway Production Environment
DATABASE_URL=sqlite+aiosqlite:///./railway_db.sqlite
TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY
OPENAI_API_KEY=your_openai_key_here
ENVIRONMENT=production
DEBUG=False
PYTHONPATH=/app
PYTHONUNBUFFERED=1
""")
    print("✅ Создан railway.env")

def update_nixpacks_config():
    """Обновляем nixpacks для работы с SQLite"""
    
    nixpacks_content = """[providers]
python = "3.11"

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[variables]
PYTHONPATH = "/app"
PYTHONUNBUFFERED = "1"
DATABASE_URL = "sqlite+aiosqlite:///./railway_db.sqlite"

[phases.build]
cmds = [
    "pip install -r requirements.txt",
    "mkdir -p /app/db"
]

[phases.setup]
nixPkgs = [
    "python311",
    "python311Packages.pip"
]"""
    
    with open("nixpacks.toml", "w") as f:
        f.write(nixpacks_content)
    print("✅ Обновлён nixpacks.toml для SQLite")

if __name__ == "__main__":
    print("🔧 Исправление конфигурации Railway для работы с SQLite")
    print("=" * 60)
    
    fix_database_config()
    update_nixpacks_config()
    
    print("\n🎉 Исправления применены!")
    print("\n📝 Следующие шаги:")
    print("1. git add .")
    print("2. git commit -m '🔧 Add SQLite fallback for Railway'")
    print("3. git push origin main")
    print("4. Дождитесь нового деплоя в Railway")
    print("\n⚠️  ВАЖНО: После успешного деплоя добавьте переменные окружения в Railway UI:")
    print("   - DATABASE_URL=sqlite+aiosqlite:///./railway_db.sqlite")
    print("   - OPENAI_API_KEY=ваш_ключ") 