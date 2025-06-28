// M² Calendar Mini App - Events Management
class EventManager {
    constructor(calendar) {
        this.calendar = calendar;
        this.apiUrl = '/api/v1';
        this.userId = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.getUserId();
    }

    setupEventListeners() {
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => this.calendar.hideModal('eventModal'));
        document.getElementById('closeDetailsModal').addEventListener('click', () => this.calendar.hideModal('eventDetailsModal'));
        document.getElementById('cancelEvent').addEventListener('click', () => this.calendar.hideModal('eventModal'));
        
        // Form submission
        document.getElementById('eventForm').addEventListener('submit', (e) => this.handleEventSubmit(e));
        
        // Event actions
        document.getElementById('editEventBtn').addEventListener('click', () => this.editEvent());
        document.getElementById('deleteEventBtn').addEventListener('click', () => this.deleteEvent());
        
        // Click outside modal to close
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.calendar.hideModal(modal.id);
                }
            });
        });
    }

    getUserId() {
        if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
            this.userId = window.Telegram.WebApp.initDataUnsafe.user.id;
        } else {
            // Для тестирования без Telegram
            this.userId = 'demo_user';
        }
    }

    async handleEventSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const eventData = {
            title: formData.get('eventTitle') || document.getElementById('eventTitle').value,
            date: formData.get('eventDate') || document.getElementById('eventDate').value,
            time: formData.get('eventTime') || document.getElementById('eventTime').value,
            duration: parseInt(formData.get('eventDuration') || document.getElementById('eventDuration').value),
            type: formData.get('eventType') || document.getElementById('eventType').value,
            location: formData.get('eventLocation') || document.getElementById('eventLocation').value,
            client: formData.get('eventClient') || document.getElementById('eventClient').value,
            description: formData.get('eventDescription') || document.getElementById('eventDescription').value,
            reminder: document.getElementById('eventReminder').checked
        };

        // Валидация
        if (!eventData.title || !eventData.date || !eventData.time) {
            this.showError('Заполните обязательные поля');
            return;
        }

        try {
            document.getElementById('loadingOverlay').classList.remove('hidden');
            
            const event = await this.createEvent(eventData);
            
            // Добавляем событие в календарь
            this.addEventToCalendar(event);
            
            // Закрываем модальное окно
            this.calendar.hideModal('eventModal');
            
            // Обновляем календарь
            this.calendar.renderCalendar();
            
            this.showSuccess('Событие создано!');
            
        } catch (error) {
            console.error('Error creating event:', error);
            this.showError('Ошибка при создании события');
        } finally {
            document.getElementById('loadingOverlay').classList.add('hidden');
        }
    }

    async createEvent(eventData) {
        // Для демонстрации создаем событие локально
        const event = {
            id: Date.now(),
            title: eventData.title,
            date: eventData.date,
            time: eventData.time,
            type: eventData.type,
            location: eventData.location,
            client: eventData.client,
            description: eventData.description,
            duration: eventData.duration,
            reminder: eventData.reminder,
            created_at: new Date().toISOString()
        };

        // В реальном приложении здесь был бы API запрос:
        /*
        const response = await fetch(`${this.apiUrl}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({
                ...eventData,
                user_id: this.userId
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create event');
        }

        return await response.json();
        */

        return event;
    }

    addEventToCalendar(event) {
        if (!this.calendar.events.has(event.date)) {
            this.calendar.events.set(event.date, []);
        }
        this.calendar.events.get(event.date).push(event);
    }

    async loadEvents() {
        try {
            // В реальном приложении загружаем с сервера:
            /*
            const response = await fetch(`${this.apiUrl}/events?user_id=${this.userId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load events');
            }

            const events = await response.json();
            */

            // Для демонстрации используем примеры событий
            const events = this.getSampleEvents();
            
            // Группируем события по датам
            this.calendar.events.clear();
            events.forEach(event => {
                if (!this.calendar.events.has(event.date)) {
                    this.calendar.events.set(event.date, []);
                }
                this.calendar.events.get(event.date).push(event);
            });

            this.calendar.renderCalendar();
            
        } catch (error) {
            console.error('Failed to load events:', error);
            this.showError('Ошибка загрузки событий');
        }
    }

    getSampleEvents() {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        
        const dayAfterTomorrow = new Date(today);
        dayAfterTomorrow.setDate(today.getDate() + 2);

        return [
            {
                id: 1,
                title: 'Встреча с Ивановым',
                date: this.calendar.formatDate(today),
                time: '15:00',
                type: 'meeting',
                location: 'В офисе',
                client: 'Иванов И.И.',
                description: 'Обсуждение покупки квартиры в центре'
            },
            {
                id: 2,
                title: 'Показ квартиры',
                date: this.calendar.formatDate(tomorrow),
                time: '10:00',
                type: 'showing',
                location: 'ул. Пушкина, 10',
                client: 'Петров П.П.',
                description: '2-комнатная квартира, 65 кв.м.'
            },
            {
                id: 3,
                title: 'Звонок клиенту',
                date: this.calendar.formatDate(tomorrow),
                time: '14:30',
                type: 'call',
                client: 'Сидорова А.В.',
                description: 'Уточнить детали по ипотеке'
            },
            {
                id: 4,
                title: 'Подписание договора',
                date: this.calendar.formatDate(dayAfterTomorrow),
                time: '11:00',
                type: 'deal',
                location: 'Нотариус, ул. Ленина, 15',
                client: 'Козлов В.М.',
                description: 'Сделка по продаже дома'
            }
        ];
    }

    showEventDetails(event) {
        const modal = document.getElementById('eventDetailsModal');
        const detailsContainer = document.getElementById('eventDetails');
        
        const typeIcons = {
            meeting: '🤝',
            showing: '🏠',
            call: '📞',
            deal: '💰',
            task: '📋',
            other: '📝'
        };

        detailsContainer.innerHTML = `
            <div class="event-detail-item">
                <div class="detail-label">Событие</div>
                <div class="detail-value">${typeIcons[event.type] || '📝'} ${event.title}</div>
            </div>
            
            <div class="event-detail-item">
                <div class="detail-label">Дата и время</div>
                <div class="detail-value">📅 ${this.formatDate(event.date)} в ${event.time}</div>
            </div>
            
            ${event.location ? `
                <div class="event-detail-item">
                    <div class="detail-label">Место</div>
                    <div class="detail-value">📍 ${event.location}</div>
                </div>
            ` : ''}
            
            ${event.client ? `
                <div class="event-detail-item">
                    <div class="detail-label">Клиент</div>
                    <div class="detail-value">👤 ${event.client}</div>
                </div>
            ` : ''}
            
            ${event.description ? `
                <div class="event-detail-item">
                    <div class="detail-label">Описание</div>
                    <div class="detail-value">${event.description}</div>
                </div>
            ` : ''}
        `;

        // Сохраняем текущее событие для редактирования/удаления
        this.currentEvent = event;
        
        this.calendar.showModal('eventDetailsModal');
    }

    editEvent() {
        if (!this.currentEvent) return;
        
        // Заполняем форму данными события
        document.getElementById('eventTitle').value = this.currentEvent.title;
        document.getElementById('eventDate').value = this.currentEvent.date;
        document.getElementById('eventTime').value = this.currentEvent.time;
        document.getElementById('eventType').value = this.currentEvent.type;
        document.getElementById('eventLocation').value = this.currentEvent.location || '';
        document.getElementById('eventClient').value = this.currentEvent.client || '';
        document.getElementById('eventDescription').value = this.currentEvent.description || '';
        
        // Меняем заголовок модального окна
        document.getElementById('modalTitle').textContent = 'Редактировать событие';
        
        // Закрываем детали и открываем форму
        this.calendar.hideModal('eventDetailsModal');
        this.calendar.showModal('eventModal');
    }

    async deleteEvent() {
        if (!this.currentEvent) return;

        const confirmed = window.Telegram?.WebApp ? 
            await new Promise(resolve => {
                window.Telegram.WebApp.showConfirm('Удалить событие?', resolve);
            }) : 
            confirm('Удалить событие?');

        if (!confirmed) return;

        try {
            document.getElementById('loadingOverlay').classList.remove('hidden');
            
            // В реальном приложении отправляем запрос на сервер:
            /*
            const response = await fetch(`${this.apiUrl}/events/${this.currentEvent.id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete event');
            }
            */

            // Удаляем событие из локального хранилища
            this.removeEventFromCalendar(this.currentEvent);
            
            // Закрываем модальное окно
            this.calendar.hideModal('eventDetailsModal');
            
            // Обновляем календарь
            this.calendar.renderCalendar();
            
            this.showSuccess('Событие удалено!');
            
        } catch (error) {
            console.error('Error deleting event:', error);
            this.showError('Ошибка при удалении события');
        } finally {
            document.getElementById('loadingOverlay').classList.add('hidden');
        }
    }

    removeEventFromCalendar(event) {
        const dayEvents = this.calendar.events.get(event.date);
        if (dayEvents) {
            const index = dayEvents.findIndex(e => e.id === event.id);
            if (index > -1) {
                dayEvents.splice(index, 1);
                if (dayEvents.length === 0) {
                    this.calendar.events.delete(event.date);
                }
            }
        }
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    }

    showSuccess(message) {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.showAlert(message);
        } else {
            // Создаем кастомное уведомление
            this.showNotification(message, 'success');
        }
    }

    showError(message) {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.showAlert(message);
        } else {
            this.showNotification(message, 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 16px;
            right: 16px;
            z-index: 10000;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideDown 0.3s ease;
        `;

        // Добавляем на страницу
        document.body.appendChild(notification);

        // Автоматическое скрытие через 3 секунды
        setTimeout(() => {
            notification.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);

        // Закрытие по клику
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    getAuthToken() {
        // В реальном приложении здесь будет получение токена
        return 'demo_token';
    }
}

// Экспорт для использования
window.EventManager = EventManager;
