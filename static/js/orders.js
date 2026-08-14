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
    // 3. УДАЛЕНИЕ ЗАКАЗА
    // =========================================================
    const deleteOrderBtns = document.querySelectorAll('.delete-order');
    deleteOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
            if (confirm(`Вы уверены, что хотите удалить заказ ${orderNumber}?`)) {
                const deleteUrl = `/orders/${orderPk}/delete/`;
                fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || getCookie('csrftoken'),
                    },
                }).then(response => {
                    if (response.ok) {
                        window.location.href = '/orders/';
                    } else {
                        alert('Ошибка при удалении заказа');
                    }
                }).catch(error => {
                    alert('Ошибка при удалении заказа');
                });
            }
        });
    });

    // =========================================================
    // 4. ЗАГРУЗКА ФАЙЛОВ К ЗАКАЗУ
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
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
                uploadBtn.disabled = true;
                
                fetch(`/orders/${orderPk}/upload/`, {
                    method: 'POST',
                    body: formData,
                })
                .then(response => response.json())
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
                        
                        // Показываем уведомление
                        const toast = createToast('Файлы успешно загружены!', 'success');
                        document.body.appendChild(toast);
                        setTimeout(() => toast.remove(), 3000);
                    } else {
                        alert('Ошибка загрузки: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Ошибка загрузки файлов');
                })
                .finally(() => {
                    uploadBtn.innerHTML = '<i class="fas fa-upload me-1"></i>Загрузить';
                    uploadBtn.disabled = false;
                });
            });
            
            fileInput.click();
        });
    }

    // =========================================================
    // 5. ЗАПУСК ЗАКАЗА (заглушка)
    // =========================================================
    const startOrderBtns = document.querySelectorAll('.start-order');
    startOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
            // TODO: реализовать логику запуска заказа
            const toast = createToast(`Функция "Запустить заказ ${orderNumber}" будет реализована в следующей версии.`, 'info');
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        });
    });

    // =========================================================
    // 6. ПРОГРЕСС-БАР В КАРТОЧКЕ ЗАКАЗА (автообновление)
    // =========================================================
    // Если есть элемент с id="orderProgress", можно обновлять его через AJAX
    // Пока оставляем как есть (статический прогресс из вьюхи)

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

    // Создание уведомления (toast)
    function createToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = `
            top: 80px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        return toast;
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
            this.closest('form').submit();
        });
    }

    console.log('📦 Заказы загружены');
});