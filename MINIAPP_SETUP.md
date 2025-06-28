# 🗓️ М² Календарь - Telegram Mini App

## Статус: ✅ ГОТОВ К ИСПОЛЬЗОВАНИЮ

### 📱 Что создано:

1. **Полноценный Mini App календарь** с современным дизайном М²
2. **API endpoints** для интеграции с основным приложением
3. **Кнопки в боте** для запуска Mini App
4. **Адаптивный интерфейс** для мобильных устройств

### 🌐 Текущие URL (для тестирования):

- **API:** http://127.0.0.1:8000/api/v1/miniapp/
- **Демо-версия:** file:///.../calc/miniapp/demo.html

### 🎨 Функции календаря:

- ✅ **3 вида отображения**: Месяц, Неделя, День
- ✅ **Создание событий** с полной формой
- ✅ **Типы событий**: Встречи 🤝, Показы 🏠, Звонки 📞, Сделки 💰
- ✅ **Навигация** по датам
- ✅ **Цветовая индикация** событий
- ✅ **Модальные окна** для создания и просмотра
- ✅ **Синхронизация** с основным ботом
- ✅ **Telegram интеграция** (темы, haptic feedback)

### 🚀 Быстрый запуск (уже работает):

```bash
# 1. API сервер уже запущен на порту 8000
curl http://127.0.0.1:8000/api/v1/miniapp/

# 2. Откройте в браузере для тестирования:
open http://127.0.0.1:8000/api/v1/miniapp/

# 3. Демо-версия:
open miniapp/demo.html
```

### 🛠 Настройка для продакшена:

#### 1. Домен и HTTPS
```bash
# Обновите URL в кнопках бота:
# app/bot/keyboards/calendar.py
# app/bot/keyboards/reply.py

# Замените:
http://127.0.0.1:8000/api/v1/miniapp/
# На:
https://yourdomain.com/api/v1/miniapp/
```

#### 2. Nginx конфигурация
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    location /api/v1/miniapp/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 🔧 Доступные API endpoints:

- `GET /api/v1/miniapp/` - HTML страница Mini App
- `GET /api/v1/miniapp/static/css/calendar.css` - Стили
- `GET /api/v1/miniapp/static/js/*.js` - JavaScript файлы
- `GET /api/v1/miniapp/events` - Получение событий
- `POST /api/v1/miniapp/events` - Создание события
- `DELETE /api/v1/miniapp/events/{id}` - Удаление события
- `POST /api/v1/miniapp/sync` - Синхронизация

### 📱 Интеграция с Telegram:

#### В главном меню бота:
- Кнопка **"🗓️ Календарь М²"** (WebApp)

#### В быстрых действиях:
- Кнопка **"🗓️ Открыть календарь"** (WebApp)

### 🎯 Telegram Web App особенности:

- ✅ **Автоматическая тема** (светлая/темная)
- ✅ **Haptic feedback** при нажатиях
- ✅ **Main Button** для быстрого создания событий
- ✅ **Back Button** для навигации
- ✅ **Полноэкранный режим** с expand()

---

## 🎉 Готово!

Mini App календарь полностью готов и интегрирован с вашим Telegram ботом. 
Современный дизайн, полный функционал и отличный UX! 🚀
