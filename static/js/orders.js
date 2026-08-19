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

    // Закрываем сайдбар при клике вне его
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const isClickInside = sidebar.contains(e.target) || sidebarToggle?.contains(e.target);
            if (!isClickInside && sidebar.classList.contains('show')) {
                toggleSidebar();
            }
        }
    });

    // =========================================================
    // 2. АВТОМАТИЧЕСКОЕ СКРЫТИЕ ALERT-СООБЩЕНИЙ
    // =========================================================
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            } else {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 500);
            }
        }, 5000);
    });

    // =========================================================
    // 3. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
    // =========================================================
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.message || 'Вы уверены, что хотите удалить этот объект?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

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

// Создание уведомления (toast)
function showToast(message, type = 'info', duration = 3000) {
    document.querySelectorAll('.custom-toast').forEach(el => el.remove());
    
    const types = {
        success: 'check-circle',
        danger: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = `
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease;
    `;
    toast.innerHTML = `
        <i class="fas fa-${types[type] || 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => {
            const closeBtn = toast.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
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