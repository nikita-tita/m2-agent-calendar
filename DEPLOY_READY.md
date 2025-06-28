# 🚀 ГОТОВЫЕ КОМАНДЫ ДЛЯ ДЕПЛОЯ

## 📋 ШАГ 1: GITHUB (СКОПИРОВАТЬ В ТЕРМИНАЛ)

```bash
# Создаем репозиторий на GitHub
gh repo create m2-agent-calendar --public --description "M² Agent Calendar - Telegram Bot for Real Estate Agents"

# Загружаем код
git remote add origin https://github.com/$(gh api user --jq .login)/m2-agent-calendar.git
git branch -M main  
git push -u origin main

echo "✅ GitHub готов!"
```

**Если нет GitHub CLI:**
1. Зайти на https://github.com/new
2. Repository name: `m2-agent-calendar`  
3. Public ✅
4. Create repository
5. Скопировать URL и выполнить:

```bash
git remote add origin YOUR_GITHUB_URL_HERE
git branch -M main
git push -u origin main
```

---

## 🚂 ШАГ 2А: RAILWAY.APP (РЕКОМЕНДУЕТСЯ)

### В браузере:
1. Открыть https://railway.app/new
2. "Deploy from GitHub repo"
3. Выбрать `m2-agent-calendar`
4. Deploy Now

### Добавить PostgreSQL:
1. В проекте нажать "+"  
2. "Database" → "PostgreSQL"
3. Deploy

### Переменные окружения:
1. Зайти в Variables
2. Добавить по одной:

```
TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY
OPENAI_API_KEY=your_openai_key_here
```

### После деплоя:
```bash
# Скопировать PUBLIC URL из Railway и выполнить:
python auto_deploy.py https://github.com/username/m2-agent-calendar.git https://YOUR-APP.railway.app
```

---

## 🎨 ШАГ 2Б: RENDER.COM (АЛЬТЕРНАТИВА)

### В браузере:
1. Открыть https://render.com/dashboard
2. "New" → "Web Service"
3. "Build and deploy from a Git repository"
4. Connect GitHub → выбрать `m2-agent-calendar`

### Настройки:
- **Name:** `m2-agent-calendar`
- **Build Command:** `pip install -r requirements.txt`  
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables:
```
TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY
OPENAI_API_KEY=your_openai_key_here
```

### Добавить PostgreSQL:
1. "New" → "PostgreSQL"  
2. Скопировать DATABASE_URL в переменные веб-сервиса

---

## 🔥 ШАГ 2В: HEROKU (КЛАССИКА)

### В браузере:
1. https://dashboard.heroku.com/new-app
2. App name: `m2-agent-calendar-[random]`
3. Create app

### Deploy:
1. Deploy → GitHub
2. Connect to GitHub → выбрать репозиторий
3. Enable Automatic Deploys  
4. Deploy Branch

### Add-ons:
1. Resources → Add-ons
2. Heroku Postgres → Install

### Config Vars:
```
TELEGRAM_BOT_TOKEN=7794113902:AAHIPTjgr1ZI5dz1b7m0P6xQK_NhmAKQ1KY
OPENAI_API_KEY=your_openai_key_here
```

---

## 🔗 ШАГ 3: АВТОНАСТРОЙКА WEBHOOK

После получения URL выполнить:

```bash
# Railway
python setup_webhook.py https://your-app.railway.app

# Render  
python setup_webhook.py https://your-app.onrender.com

# Heroku
python setup_webhook.py https://your-app.herokuapp.com
```

---

## 🧪 ШАГ 4: ФИНАЛЬНАЯ ПРОВЕРКА

```bash
# Проверка API
curl https://your-domain.com/health

# Проверка Mini App
curl https://your-domain.com/api/v1/miniapp/

# Тест в Telegram: /start @m2_agentcalendar_bot
```

---

## 🎉 ГОТОВО!

После выполнения всех шагов:
- ✅ Бот работает в Telegram
- ✅ Mini App доступен  
- ✅ База данных подключена
- ✅ Webhook настроен
- ✅ Система готова к использованию! 