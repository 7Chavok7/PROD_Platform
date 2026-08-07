/**
 * ProdPlatform — Основной JavaScript
 * Автор: A.Grachev
 * Версия: 0.3
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // ============================================================
    // 1. ТОГГЛ САЙДБАРА (МОБИЛЬНАЯ ВЕРСИЯ)
    // ============================================================
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

    // ============================================================
    // 2. АВТОМАТИЧЕСКОЕ СКРЫТИЕ ALERT-СООБЩЕНИЙ
    // ============================================================
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

    // ============================================================
    // 3. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
    // ============================================================
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.message || 'Вы уверены, что хотите удалить этот объект?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ============================================================
    // 4. АВТОЗАПОЛНЕНИЕ ПОЛЕЙ (ДЛЯ ИМПОРТА)
    // ============================================================
    const importFileInput = document.getElementById('importFile');
    if (importFileInput) {
        importFileInput.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Файл не выбран';
            const label = document.querySelector('.custom-file-label');
            if (label) {
                label.textContent = fileName;
            }
        });
    }

    // ============================================================
    // 5. ПОИСК С ЗАДЕРЖКОЙ (DEBOUNCE)
    // ============================================================
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let timeoutId = null;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(function() {
                const form = searchInput.closest('form');
                if (form) {
                    form.submit();
                }
            }, 500);
        });
    }

    // ============================================================
    // 6. АКТИВНОЕ СОСТОЯНИЕ МЕНЮ (ПОДСВЕТКА)
    // ============================================================
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
        // Для главной страницы
        if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // ============================================================
    // 7. ТУЛТИПЫ (Bootstrap)
    // ============================================================
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(element) {
        return new bootstrap.Tooltip(element);
    });

    // ============================================================
    // 8. СОРТИРОВКА ТАБЛИЦ (ПРОСТАЯ)
    // ============================================================
    const sortableTables = document.querySelectorAll('.sortable-table');
    sortableTables.forEach(function(table) {
        const headers = table.querySelectorAll('thead th[data-sort]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.dataset.sort;
                const isAsc = this.classList.contains('asc');
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));

                // Сортируем
                rows.sort(function(a, b) {
                    const aValue = a.querySelector(`td[data-column="${column}"]`)?.textContent.trim() || '';
                    const bValue = b.querySelector(`td[data-column="${column}"]`)?.textContent.trim() || '';
                    return isAsc
                        ? aValue.localeCompare(bValue, 'ru')
                        : bValue.localeCompare(aValue, 'ru');
                });

                // Обновляем таблицу
                rows.forEach(function(row) {
                    tbody.appendChild(row);
                });

                // Обновляем классы
                headers.forEach(function(h) {
                    h.classList.remove('asc', 'desc');
                });
                this.classList.toggle('asc', !isAsc);
                this.classList.toggle('desc', isAsc);
            });
        });
    });

    console.log('ProdPlatform загружен успешно! 🚀');
});