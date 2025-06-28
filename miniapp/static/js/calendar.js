// M² Calendar Mini App - Calendar Logic
class M2Calendar {
    constructor() {
        this.currentDate = new Date();
        this.currentView = 'month';
        this.events = new Map();
        this.selectedDate = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initTelegramWebApp();
        this.renderCalendar();
        this.loadEvents();
    }

    initTelegramWebApp() {
        if (window.Telegram && window.Telegram.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.ready();
            
            // Настройка темы
            document.documentElement.style.setProperty('--tg-theme-bg-color', tg.backgroundColor);
            document.documentElement.style.setProperty('--tg-theme-text-color', tg.textColor);
            document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.secondaryBackgroundColor);
        }
    }

    setupEventListeners() {
        // View switcher
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });

        // Navigation
        document.getElementById('prevBtn').addEventListener('click', () => this.navigatePrev());
        document.getElementById('nextBtn').addEventListener('click', () => this.navigateNext());
        document.getElementById('todayBtn').addEventListener('click', () => this.goToToday());

        // Quick actions
        document.getElementById('createEventBtn').addEventListener('click', () => this.showCreateEventModal());
        document.getElementById('syncBtn').addEventListener('click', () => this.syncEvents());
    }

    switchView(view) {
        document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-view="${view}"]`).classList.add('active');

        document.querySelectorAll('.calendar-view').forEach(v => v.classList.add('hidden'));
        
        this.currentView = view;
        
        switch (view) {
            case 'month':
                document.getElementById('monthView').classList.remove('hidden');
                this.renderMonth();
                break;
            case 'week':
                document.getElementById('weekView').classList.remove('hidden');
                this.renderWeek();
                break;
            case 'day':
                document.getElementById('dayView').classList.remove('hidden');
                this.renderDay();
                break;
        }
    }

    renderCalendar() {
        this.updatePeriodDisplay();
        
        switch (this.currentView) {
            case 'month':
                this.renderMonth();
                break;
            case 'week':
                this.renderWeek();
                break;
            case 'day':
                this.renderDay();
                break;
        }
    }

    renderMonth() {
        const container = document.getElementById('calendarDays');
        container.innerHTML = '';

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        const startDate = new Date(firstDay);
        const dayOfWeek = (firstDay.getDay() + 6) % 7;
        startDate.setDate(firstDay.getDate() - dayOfWeek);
        
        for (let i = 0; i < 42; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            const dayElement = this.createDayElement(currentDate, month);
            container.appendChild(dayElement);
        }
    }

    createDayElement(date, currentMonth) {
        const day = document.createElement('div');
        day.className = 'calendar-day';
        
        const isToday = this.isToday(date);
        const isOtherMonth = date.getMonth() !== currentMonth;
        
        if (isToday) day.classList.add('today');
        if (isOtherMonth) day.classList.add('other-month');
        
        day.innerHTML = `
            <div class="day-number">${date.getDate()}</div>
            <div class="day-events" id="events-${this.formatDate(date)}"></div>
        `;
        
        day.addEventListener('click', () => {
            this.selectDate(date);
        });
        
        this.renderDayEvents(date);
        
        return day;
    }

    renderDayEvents(date) {
        const dateStr = this.formatDate(date);
        const container = document.getElementById(`events-${dateStr}`);
        if (!container) return;
        
        const dayEvents = this.getEventsForDate(date);
        container.innerHTML = '';
        
        dayEvents.slice(0, 3).forEach(event => {
            const eventDot = document.createElement('div');
            eventDot.className = `event-dot ${event.type}`;
            eventDot.title = `${event.time} - ${event.title}`;
            container.appendChild(eventDot);
        });
        
        if (dayEvents.length > 3) {
            const moreElement = document.createElement('div');
            moreElement.className = 'event-more';
            moreElement.textContent = `+${dayEvents.length - 3}`;
            container.appendChild(moreElement);
        }
    }

    renderWeek() {
        const container = document.getElementById('weekDays');
        container.innerHTML = '';
        
        const weekStart = this.getWeekStart(this.currentDate);
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(weekStart);
            date.setDate(weekStart.getDate() + i);
            
            const dayColumn = this.createWeekDayColumn(date);
            container.appendChild(dayColumn);
        }
    }

    createWeekDayColumn(date) {
        const column = document.createElement('div');
        column.className = 'week-day';
        
        const isToday = this.isToday(date);
        
        column.innerHTML = `
            <div class="week-day-header ${isToday ? 'today' : ''}">
                <div class="day-name">${this.getDayName(date)}</div>
                <div class="day-number">${date.getDate()}</div>
            </div>
            <div class="week-hours" id="week-${this.formatDate(date)}"></div>
        `;
        
        const hoursContainer = column.querySelector('.week-hours');
        for (let hour = 0; hour < 24; hour++) {
            const hourSlot = document.createElement('div');
            hourSlot.className = 'week-hour';
            hourSlot.dataset.hour = hour;
            hourSlot.addEventListener('click', () => {
                this.createEventAtTime(date, hour);
            });
            hoursContainer.appendChild(hourSlot);
        }
        
        return column;
    }

    renderDay() {
        const container = document.getElementById('daySchedule');
        container.innerHTML = '';
        
        const dayEvents = this.getEventsForDate(this.currentDate);
        dayEvents.sort((a, b) => a.time.localeCompare(b.time));
        
        if (dayEvents.length === 0) {
            container.innerHTML = `
                <div class="empty-day">
                    <p>На этот день событий нет</p>
                    <button class="btn-primary" onclick="window.calendar.showCreateEventModal()">
                        Создать событие
                    </button>
                </div>
            `;
            return;
        }
        
        dayEvents.forEach(event => {
            const eventElement = this.createDayEventElement(event);
            container.appendChild(eventElement);
        });
    }

    createDayEventElement(event) {
        const element = document.createElement('div');
        element.className = `day-event ${event.type}`;
        element.innerHTML = `
            <div class="event-time">${event.time}</div>
            <div class="event-content">
                <div class="event-title">${event.title}</div>
                ${event.location ? `<div class="event-location">📍 ${event.location}</div>` : ''}
                ${event.client ? `<div class="event-client">👤 ${event.client}</div>` : ''}
            </div>
        `;
        
        return element;
    }

    updatePeriodDisplay() {
        const periodElement = document.getElementById('currentPeriod');
        
        switch (this.currentView) {
            case 'month':
                periodElement.textContent = this.currentDate.toLocaleDateString('ru-RU', {
                    month: 'long',
                    year: 'numeric'
                });
                break;
            case 'week':
                const weekStart = this.getWeekStart(this.currentDate);
                const weekEnd = new Date(weekStart);
                weekEnd.setDate(weekStart.getDate() + 6);
                periodElement.textContent = `${weekStart.getDate()} - ${weekEnd.getDate()} ${weekEnd.toLocaleDateString('ru-RU', { month: 'long' })}`;
                break;
            case 'day':
                periodElement.textContent = this.currentDate.toLocaleDateString('ru-RU', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long'
                });
                break;
        }
    }

    navigatePrev() {
        switch (this.currentView) {
            case 'month':
                this.currentDate.setMonth(this.currentDate.getMonth() - 1);
                break;
            case 'week':
                this.currentDate.setDate(this.currentDate.getDate() - 7);
                break;
            case 'day':
                this.currentDate.setDate(this.currentDate.getDate() - 1);
                break;
        }
        this.renderCalendar();
    }

    navigateNext() {
        switch (this.currentView) {
            case 'month':
                this.currentDate.setMonth(this.currentDate.getMonth() + 1);
                break;
            case 'week':
                this.currentDate.setDate(this.currentDate.getDate() + 7);
                break;
            case 'day':
                this.currentDate.setDate(this.currentDate.getDate() + 1);
                break;
        }
        this.renderCalendar();
    }

    goToToday() {
        this.currentDate = new Date();
        this.renderCalendar();
    }

    selectDate(date) {
        document.querySelectorAll('.calendar-day.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        this.selectedDate = new Date(date);
        this.currentDate = new Date(date);
        this.switchView('day');
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    isToday(date) {
        const today = new Date();
        return this.isSameDay(date, today);
    }

    isSameDay(date1, date2) {
        return date1.getDate() === date2.getDate() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getFullYear() === date2.getFullYear();
    }

    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(d.setDate(diff));
    }

    getDayName(date) {
        return date.toLocaleDateString('ru-RU', { weekday: 'short' });
    }

    getEventsForDate(date) {
        const dateStr = this.formatDate(date);
        return this.events.get(dateStr) || [];
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
    }

    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showCreateEventModal(date = null, time = null) {
        const form = document.getElementById('eventForm');
        form.reset();
        
        if (date) {
            document.getElementById('eventDate').value = this.formatDate(date);
        } else if (this.selectedDate) {
            document.getElementById('eventDate').value = this.formatDate(this.selectedDate);
        } else {
            document.getElementById('eventDate').value = this.formatDate(new Date());
        }
        
        if (time !== null) {
            document.getElementById('eventTime').value = `${time.toString().padStart(2, '0')}:00`;
        }
        
        this.showModal('eventModal');
    }

    createEventAtTime(date, hour) {
        this.showCreateEventModal(date, hour);
    }

    async loadEvents() {
        // Загрузка событий с сервера
        try {
            // Пример данных для демонстрации
            const sampleEvents = [
                {
                    id: 1,
                    title: 'Встреча с Ивановым',
                    date: '2024-12-19',
                    time: '15:00',
                    type: 'meeting',
                    location: 'В офисе',
                    client: 'Иванов И.И.'
                },
                {
                    id: 2,
                    title: 'Показ квартиры',
                    date: '2024-12-20',
                    time: '10:00',
                    type: 'showing',
                    location: 'ул. Пушкина, 10',
                    client: 'Петров П.П.'
                }
            ];
            
            sampleEvents.forEach(event => {
                if (!this.events.has(event.date)) {
                    this.events.set(event.date, []);
                }
                this.events.get(event.date).push(event);
            });
            
            this.renderCalendar();
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    }

    async syncEvents() {
        document.getElementById('loadingOverlay').classList.remove('hidden');
        
        try {
            // Имитация синхронизации
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            if (window.Telegram?.WebApp) {
                window.Telegram.WebApp.showAlert('События синхронизированы!');
            } else {
                alert('События синхронизированы!');
            }
        } catch (error) {
            console.error('Sync failed:', error);
            if (window.Telegram?.WebApp) {
                window.Telegram.WebApp.showAlert('Ошибка синхронизации');
            } else {
                alert('Ошибка синхронизации');
            }
        } finally {
            document.getElementById('loadingOverlay').classList.add('hidden');
        }
    }
}

window.M2Calendar = M2Calendar;
