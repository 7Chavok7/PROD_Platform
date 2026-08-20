/* static/js/main.js | A.Grachev */
// =========================================================
//   ОСНОВНАЯ ЛОГИКА (ГЛОБАЛЬНЫЕ ФУНКЦИИ)
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // =========================================================
    // 1. ТОГГЛ САЙДБАРА (МОБИЛЬНАЯ ВЕРСИЯ)
    // =========================================================
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(backdrop);

    function toggleSidebar() {
        sidebar.classList.toggle('show');
        backdrop.classList.toggle('show');
        document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    backdrop.addEventListener('click', toggleSidebar);

    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const isClickInside = sidebar.contains(e.target) || sidebarToggle?.contains(e.target);
            if (!isClickInside && sidebar.classList.contains('show')) {
                toggleSidebar();
            }
        }
    });

    // =========================================================
    // 2. ПРЕОБРАЗОВАНИЕ ALERT В TOAST
    // =========================================================
    function convertAlertsToToasts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            // Определяем тип
            let type = 'info';
            if (alert.classList.contains('alert-success')) type = 'success';
            else if (alert.classList.contains('alert-danger')) type = 'error';
            else if (alert.classList.contains('alert-warning')) type = 'warning';
            else if (alert.classList.contains('alert-info')) type = 'info';
            
            // Получаем текст и иконку
            const icon = alert.querySelector('i');
            const text = alert.textContent.trim();
            
            // Создаем toast
            const toast = document.createElement('div');
            toast.className = `custom-toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                    <span>${text}</span>
                </div>
                <button class="toast-close">&times;</button>
            `;
            
            // Добавляем в body
            document.body.appendChild(toast);
            
            // Показываем с анимацией
            setTimeout(() => toast.classList.add('show'), 50);
            
            // Закрываем через 4 секунды
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
            
            // Закрытие по кнопке
            toast.querySelector('.toast-close').addEventListener('click', function() {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            });
            
            // Удаляем оригинальный alert
            alert.remove();
        });
    }
    
    // Запускаем конвертацию после загрузки
    convertAlertsToToasts();

    // =========================================================
    // 3. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
    // =========================================================
    // const deleteButtons = document.querySelectorAll('.confirm-delete');
    // deleteButtons.forEach(function(btn) {
    //     btn.addEventListener('click', function(e) {
    //         const message = this.dataset.message || 'Вы уверены, что хотите удалить этот объект?';
    //         if (!confirm(message)) {
    //             e.preventDefault();
    //         }
    //     });
    // });

    // =========================================================
    // 4. АКТИВНОЕ СОСТОЯНИЕ МЕНЮ (ПОДСВЕТКА)
    // =========================================================
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link:not(.dropdown-toggle)');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && href !== '/') {
            if (currentPath === href || currentPath.startsWith(href + '/')) {
                link.classList.add('active');
            }
        }
        if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // =========================================================
    // 5. ТУЛТИПЫ (Bootstrap)
    // =========================================================
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(element) {
        return new bootstrap.Tooltip(element);
    });

    // =========================================================
    // 6. АНИМАЦИЯ ПРОГРЕСС-БАРОВ
    // =========================================================
    function animateProgressBars() {
        document.querySelectorAll('.progress-mini .progress-bar').forEach(function(bar) {
            const targetWidth = bar.style.width;
            if (targetWidth && targetWidth !== '0%') {
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = targetWidth;
                }, 100);
            }
        });
    }
    
    animateProgressBars();

    console.log('🚀 ProdPlatform загружен');
});

// =========================================================
//   ГЛОБАЛЬНЫЕ УТИЛИТЫ
// =========================================================

// Получение CSRF-токена из куки
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Глобальная функция показа уведомлений
function showToast(message, type = 'info', duration = 4000) {
    // Удаляем старые уведомления
    document.querySelectorAll('.custom-toast').forEach(el => el.remove());
    
    const types = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${types[type] || 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Показываем с анимацией
    setTimeout(() => toast.classList.add('show'), 50);
    
    // Закрытие по кнопке
    toast.querySelector('.toast-close').addEventListener('click', function() {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    });
    
    // Автозакрытие
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

// Дебаунс для поиска
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
