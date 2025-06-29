#!/bin/bash

echo "🚀 Quick Push to GitHub for Railway Deploy"
echo "==========================================="

# Добавить все изменения
git add .

# Коммит с сообщением
git commit -m "🔧 Fix Railway config: Switch to Nixpacks, add proper start command"

# Пуш в main ветку
git push origin main

echo "✅ Изменения отправлены в GitHub!"
echo "🚂 Railway автоматически начнёт новый деплой"
echo ""
echo "📊 Проверить статус деплоя: https://railway.app/dashboard"
echo "🔗 После успешного деплоя используйте: python diagnose_and_fix.py" 