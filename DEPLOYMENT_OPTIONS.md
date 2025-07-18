# 🚀 Варианты развёртывания M² Agent Calendar

## 1️⃣ Railway.app (Рекомендуется) ⭐
**Время: 5-10 минут | Сложность: Легко | Стоимость: Бесплатно**

✅ Автоматический PostgreSQL  
✅ Простое развёртывание из GitHub  
✅ HTTPS из коробки  
✅ Автомасштабирование  

**Шаги:**
1. Зарегистрироваться на railway.app
2. Подключить GitHub репозиторий
3. Добавить PostgreSQL сервис
4. Установить переменные окружения
5. Развернуть!

## 2️⃣ Render.com
**Время: 7-15 минут | Сложность: Легко | Стоимость: Бесплатно**

✅ Автоматический SSL  
✅ Интеграция с GitHub  
✅ Автоматические деплои  

**Особенности:**
- Спит через 15 минут неактивности (бесплатный план)
- Поддержка Docker
- Простая настройка переменных

## 3️⃣ Heroku
**Время: 10-20 минут | Сложность: Средне | Стоимость: $7/мес**

✅ Надёжная платформа  
✅ Множество аддонов  
✅ Хорошая документация  

**Минусы:**
- Платная PostgreSQL
- Более сложная настройка

## 4️⃣ DigitalOcean App Platform
**Время: 15-30 минут | Сложность: Средне | Стоимость: $5/мес**

✅ Высокая производительность  
✅ Managed PostgreSQL  
✅ Автомасштабирование  

## 5️⃣ VPS (DigitalOcean/Linode)
**Время: 30-60 минут | Сложность: Сложно | Стоимость: $5-10/мес**

✅ Полный контроль  
✅ Максимальная производительность  
✅ Возможность кастомизации  

**Требует:**
- Настройку сервера
- Установку Docker
- Настройку nginx
- SSL сертификатов

## 📊 Сравнение платформ

| Платформа | Время | Сложность | Стоимость | Рекомендация |
|-----------|-------|-----------|-----------|--------------|
| Railway   | 5 мин | Легко     | Бесплатно | ⭐⭐⭐⭐⭐ |
| Render    | 7 мин | Легко     | Бесплатно | ⭐⭐⭐⭐ |
| Heroku    | 10 мин| Средне    | $7/мес    | ⭐⭐⭐ |
| DO Apps   | 15 мин| Средне    | $5/мес    | ⭐⭐⭐ |
| VPS       | 30 мин| Сложно    | $5/мес    | ⭐⭐ |

## 🎯 Рекомендация

**Для быстрого тестирования:** Railway.app  
**Для продакшена:** DigitalOcean или Railway Pro  
**Для изучения:** VPS с Docker 