// M² Calendar Mini App - Main Application
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация календаря
    window.calendar = new M2Calendar();
    window.eventManager = new EventManager(window.calendar);
    
    // Переопределяем методы календаря для работы с событиями
    window.calendar.loadEvents = () => window.eventManager.loadEvents();
    window.calendar.showEventDetails = (event) => window.eventManager.showEventDetails(event);
    window.calendar.handleEventSubmit = (e) => window.eventManager.handleEventSubmit(e);
    
    // Инициализация Telegram Web App
    initTelegramWebApp();
    
    // Добавляем стили для анимаций
    addAnimationStyles();
    
    // Загружаем события
    window.eventManager.loadEvents();
});

function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        
        // Разворачиваем приложение
        tg.expand();
        
        // Настройка цветовой схемы
        if (tg.colorScheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
        
        // Настройка header color
        tg.setHeaderColor('#FF6B35');
        
        // Отключаем вертикальные свайпы
        tg.enableVerticalSwipes = false;
        
        // Показываем главную кнопку для быстрого создания события
        tg.MainButton.setText('Создать событие');
        tg.MainButton.color = '#FF6B35';
        tg.MainButton.textColor = '#FFFFFF';
        tg.MainButton.show();
        
        tg.MainButton.onClick(() => {
            window.calendar.showCreateEventModal();
        });
        
        // Обработка кнопки назад
        tg.BackButton.onClick(() => {
            // Если открыто модальное окно, закрываем его
            const openModal = document.querySelector('.modal-overlay:not([style*="display: none"])');
            if (openModal) {
                window.calendar.hideModal(openModal.id);
                return;
            }
            
            // Иначе закрываем приложение
            tg.close();
        });
    }
}

function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                transform: translateY(-100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        @keyframes slideUp {
            from {
                transform: translateY(0);
                opacity: 1;
            }
            to {
                transform: translateY(-100%);
                opacity: 0;
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes scaleIn {
            from { 
                transform: scale(0.9); 
                opacity: 0; 
            }
            to { 
                transform: scale(1); 
                opacity: 1; 
            }
        }
        
        .modal-overlay {
            animation: fadeIn 0.3s ease;
        }
        
        .modal-content {
            animation: scaleIn 0.3s ease;
        }
        
        .calendar-day {
            transition: all 0.2s ease;
        }
        
        .calendar-day:hover {
            transform: scale(1.05);
        }
        
        .event-dot {
            animation: fadeIn 0.3s ease;
        }
        
        .quick-btn {
            transition: all 0.2s ease;
        }
        
        .quick-btn:active {
            transform: scale(0.95);
        }
        
        .notification {
            animation: slideDown 0.3s ease;
        }
        
        .view-btn {
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            transform: scale(1.1);
        }
        
        .event-item {
            transition: all 0.2s ease;
        }
        
        .event-item:hover {
            transform: translateX(4px);
        }
        
        /* Темная тема */
        .dark-theme {
            --m2-light: #2A2A2A;
            --m2-dark: #FFFFFF;
            --m2-border: #404040;
        }
        
        .dark-theme .calendar-grid {
            background: #1E1E1E;
        }
        
        .dark-theme .modal-content {
            background: #2A2A2A;
            color: #FFFFFF;
        }
        
        .dark-theme .form-group input,
        .dark-theme .form-group select,
        .dark-theme .form-group textarea {
            background: #404040;
            border-color: #555;
            color: #FFFFFF;
        }
        
        /* Пустой день */
        .empty-day {
            text-align: center;
            padding: 40px 20px;
            color: var(--m2-gray);
        }
        
        .empty-day p {
            margin-bottom: 20px;
            font-size: 16px;
        }
        
        /* Детали события */
        .event-detail-item {
            margin-bottom: 16px;
            padding: 12px;
            background: var(--m2-light);
            border-radius: var(--radius-md);
        }
        
        .detail-label {
            font-size: 12px;
            color: var(--m2-gray);
            margin-bottom: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .detail-value {
            font-size: 14px;
            color: var(--m2-dark);
            font-weight: 500;
        }
        
        .event-actions {
            padding: 20px;
            border-top: 1px solid var(--m2-border);
            display: flex;
            gap: 12px;
        }
        
        /* Адаптивность для очень маленьких экранов */
        @media (max-width: 360px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .calendar-header {
                padding: 8px;
            }
            
            .quick-actions {
                flex-direction: column;
                gap: 8px;
            }
            
            .view-switcher {
                flex-direction: column;
                gap: 4px;
            }
            
            .calendar-nav {
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
            }
        }
        
        /* Улучшения для touch устройств */
        @media (hover: none) and (pointer: coarse) {
            .calendar-day {
                min-height: 44px; /* Минимальный размер для touch */
            }
            
            .nav-btn {
                min-width: 44px;
                min-height: 44px;
            }
            
            .quick-btn {
                min-height: 48px;
            }
            
            .view-btn {
                min-height: 36px;
                padding: 8px 16px;
            }
        }
        
        /* Индикатор загрузки */
        .loading-events {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            color: var(--m2-gray);
        }
        
        .loading-events::before {
            content: '';
            width: 20px;
            height: 20px;
            border: 2px solid var(--m2-border);
            border-top: 2px solid var(--m2-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        /* Состояние пустого календаря */
        .empty-calendar {
            text-align: center;
            padding: 60px 20px;
            color: var(--m2-gray);
        }
        
        .empty-calendar-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        
        .empty-calendar h3 {
            margin-bottom: 8px;
            color: var(--m2-dark);
        }
        
        .empty-calendar p {
            margin-bottom: 20px;
            line-height: 1.6;
        }
    `;
    document.head.appendChild(style);
}

// Вспомогательные функции для интеграции с Telegram
window.telegramHelpers = {
    showAlert: (message) => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.showAlert(message);
        } else {
            alert(message);
        }
    },
    
    showConfirm: (message) => {
        return new Promise(resolve => {
            if (window.Telegram?.WebApp) {
                window.Telegram.WebApp.showConfirm(message, resolve);
            } else {
                resolve(confirm(message));
            }
        });
    },
    
    hapticFeedback: (type = 'light') => {
        if (window.Telegram?.WebApp?.HapticFeedback) {
            window.Telegram.WebApp.HapticFeedback.impactOccurred(type);
        }
    },
    
    sendData: (data) => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.sendData(JSON.stringify(data));
        }
    }
};

// Обработчики для улучшения UX
document.addEventListener('click', (e) => {
    // Haptic feedback для кнопок
    if (e.target.matches('button, .calendar-day, .event-item')) {
        window.telegramHelpers.hapticFeedback('light');
    }
});

// Предотвращение зума на iOS
document.addEventListener('gesturestart', (e) => {
    e.preventDefault();
});

// Улучшение производительности для scroll
let ticking = false;
document.addEventListener('scroll', () => {
    if (!ticking) {
        requestAnimationFrame(() => {
            // Можно добавить логику для оптимизации скролла
            ticking = false;
        });
        ticking = true;
    }
}, { passive: true });

console.log('🗓️ M² Calendar Mini App initialized successfully!');
