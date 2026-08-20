/* static/js/orders.js | A.Grachev */
// Заказы — интерактивность
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // =========================================================
    // 1. ПЕРЕКЛЮЧЕНИЕ СТАТУСА ЗАКАЗА (с подтверждением)
    // =========================================================
    const statusChangeForms = document.querySelectorAll('.order-status-form');
    statusChangeForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const newStatus = this.querySelector('select[name="status"]');
            if (newStatus) {
                const confirmMsg = `Вы уверены, что хотите изменить статус заказа на "${newStatus.options[newStatus.selectedIndex].text}"?`;
                if (!confirm(confirmMsg)) {
                    e.preventDefault();
                }
            }
        });
    });

    // =========================================================
    // 2. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ ЭТАПА
    // =========================================================
    const deleteStageBtns = document.querySelectorAll('.delete-stage');
    deleteStageBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот этап?')) {
                e.preventDefault();
            }
        });
    });

    // =========================================================
    // 3. УДАЛЕНИЕ ЗАКАЗА (с AJAX и улучшенной обработкой)
    // =========================================================
    const deleteOrderBtns = document.querySelectorAll('.delete-order');
    deleteOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
            if (confirm(`Вы уверены, что хотите удалить заказ ${orderNumber}?`)) {
                const deleteUrl = `/orders/${orderPk}/delete/`;
                
                // ✅ Улучшенная обработка ошибок
                fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken'),
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(() => {
                    window.location.href = '/orders/';
                })
                .catch(error => {
                    console.error('❌ Ошибка при удалении заказа:', error);
                    showToast('Ошибка при удалении заказа. Попробуйте позже.', 'danger');
                });
            }
        });
    });

    // =========================================================
    // 4. ЗАГРУЗКА ФАЙЛОВ К ЗАКАЗУ (с улучшенной обратной связью)
    // =========================================================
    const uploadBtn = document.getElementById('uploadFileBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            const orderPk = this.dataset.orderPk;
            
            // Создаём скрытый input для выбора файла
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = '.pdf,.jpg,.jpeg,.png,.dwg,.dxf,.zip,.doc,.docx,.xls,.xlsx';
            
            fileInput.addEventListener('change', function() {
                const files = this.files;
                if (files.length === 0) return;
                
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken'));
                
                // Показываем индикатор загрузки
                const originalHtml = uploadBtn.innerHTML;
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
                uploadBtn.disabled = true;
                
                // ✅ Добавлен эндпоинт для загрузки
                fetch(`/orders/${orderPk}/upload/`, {
                    method: 'POST',
                    body: formData,
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Обновляем список файлов
                        const filesContainer = document.querySelector('.card-body');
                        const noMsg = document.getElementById('noFilesMessage');
                        if (noMsg) noMsg.remove();
                        
                        // Добавляем новые файлы
                        data.files.forEach(function(file) {
                            const fileDiv = document.createElement('div');
                            fileDiv.className = 'd-flex justify-content-between align-items-center mb-2';
                            fileDiv.innerHTML = `
                                <div>
                                    <i class="fas fa-file me-1"></i>
                                    <a href="${file.url}" target="_blank" class="text-decoration-none">${file.name}</a>
                                    <br>
                                    <small class="text-muted">${file.type}</small>
                                </div>
                                <span class="text-muted small">v${file.version}</span>
                            `;
                            // Вставляем перед кнопкой (если есть)
                            const uploadBtnContainer = filesContainer.querySelector('.btn');
                            if (uploadBtnContainer) {
                                filesContainer.insertBefore(fileDiv, uploadBtnContainer);
                            } else {
                                filesContainer.appendChild(fileDiv);
                            }
                        });
                        
                        showToast('Файлы успешно загружены!', 'success');
                    } else {
                        showToast('Ошибка загрузки: ' + (data.error || 'Неизвестная ошибка'), 'danger');
                    }
                })
                .catch(error => {
                    console.error('❌ Ошибка загрузки файлов:', error);
                    showToast('Ошибка загрузки файлов. Попробуйте позже.', 'danger');
                })
                .finally(() => {
                    uploadBtn.innerHTML = originalHtml;
                    uploadBtn.disabled = false;
                });
            });
            
            fileInput.click();
        });
    }

    // =========================================================
    // 5. ЗАПУСК ЗАКАЗА (заглушка - TODO)
    // =========================================================
    const startOrderBtns = document.querySelectorAll('.start-order');
    startOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
            // TODO: реализовать логику запуска заказа
            // Пока просто показываем уведомление
            showToast(`Функция "Запустить заказ ${orderNumber}" будет реализована в следующей версии.`, 'info');
            
            /* 
            // ✅ ЗАКОММЕНТИРОВАННЫЙ КОД ДЛЯ БУДУЩЕЙ РЕАЛИЗАЦИИ
            if (confirm(`Запустить заказ ${orderNumber}?`)) {
                const originalHtml = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Запуск...';
                this.disabled = true;
                
                fetch(`/orders/${orderPk}/start/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        showToast(`Заказ ${orderNumber} успешно запущен!`, 'success');
                        setTimeout(() => window.location.reload(), 1500);
                    } else {
                        showToast(data.error || 'Ошибка при запуске заказа', 'danger');
                        this.innerHTML = originalHtml;
                        this.disabled = false;
                    }
                })
                .catch(error => {
                    console.error('❌ Ошибка при запуске заказа:', error);
                    showToast('Ошибка при запуске заказа. Попробуйте позже.', 'danger');
                    this.innerHTML = originalHtml;
                    this.disabled = false;
                });
            }
            */
        });
    });

    // =========================================================
    // 6. ПРОГРЕСС-БАР В КАРТОЧКЕ ЗАКАЗА (автообновление)
    // =========================================================
    const progressBars = document.querySelectorAll('.order-progress');
    progressBars.forEach(function(bar) {
        const orderPk = bar.dataset.orderPk;
        // ✅ Можно добавить периодическое обновление
        // setInterval(() => updateProgress(orderPk), 30000);
    });

    // =========================================================
    // 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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

    // Создание и показ уведомления (toast) - улучшенная версия
    function showToast(message, type = 'info', duration = 3000) {
        // Удаляем старые уведомления
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
        
        // Добавляем анимацию через CSS
        if (!document.getElementById('toastStyles')) {
            const style = document.createElement('style');
            style.id = 'toastStyles';
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                const closeBtn = toast.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            }, duration);
        }
        
        return toast;
    }

    // Функция обновления прогресса (для будущего использования)
    function updateProgress(orderPk) {
        fetch(`/orders/${orderPk}/progress/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const progressBar = document.querySelector(`.order-progress[data-order-pk="${orderPk}"]`);
                    if (progressBar) {
                        progressBar.style.width = data.progress + '%';
                        progressBar.textContent = data.progress + '%';
                    }
                }
            })
            .catch(error => console.error('Ошибка обновления прогресса:', error));
    }

    // =========================================================
    // 8. АВТОМАТИЧЕСКИЙ ПОДСЧЁТ ПЛАНОВЫХ ЧАСОВ (отображение)
    // =========================================================
    const totalPlannedHours = document.getElementById('totalPlannedHours');
    if (totalPlannedHours) {
        const hours = parseFloat(totalPlannedHours.dataset.total) || 0;
        totalPlannedHours.textContent = hours.toFixed(1);
    }

    // =========================================================
    // 9. МАСКА ДЛЯ ДАТ (установка минимальной даты = сегодня)
    // =========================================================
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.min = today;
        }
    });

    // =========================================================
    // 10. ФИЛЬТР СТАТУСА (быстрое переключение)
    // =========================================================
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            } else {
                // Если формы нет, делаем редирект с параметром
                const url = new URL(window.location.href);
                url.searchParams.set('status', this.value);
                window.location.href = url.toString();
            }
        });
    }

    // =========================================================
    // 11. КНОПКА "ПРИМЕНИТЬ ФИЛЬТР" (для order_list)
    // =========================================================
    const applyFilterBtn = document.getElementById('applyFilterBtn');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', function() {
            const searchInput = document.getElementById('filterSearch');
            const statusSelect = document.getElementById('filterStatus');
            const prioritySelect = document.getElementById('filterPriority');
            
            const params = new URLSearchParams();
            if (searchInput && searchInput.value.trim()) {
                params.append('search', searchInput.value.trim());
            }
            if (statusSelect && statusSelect.value) {
                params.append('status', statusSelect.value);
            }
            if (prioritySelect && prioritySelect.value) {
                params.append('priority', prioritySelect.value);
            }
            
            const url = new URL(window.location.href);
            url.search = params.toString();
            window.location.href = url.toString();
        });
    }

    // =========================================================
    // 12. КЛАВИША ENTER В ПОЛЕ ПОИСКА
    // =========================================================
    const searchInput = document.getElementById('filterSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const applyBtn = document.getElementById('applyFilterBtn');
                if (applyBtn) {
                    applyBtn.click();
                }
            }
        });
    }

    console.log('📦 Заказы загружены');
});