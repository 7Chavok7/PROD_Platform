/* static/js/orders.js | A.Grachev */
// Заказы — интерактивность
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // =========================================================
    // 1. ПЕРЕКЛЮЧЕНИЕ СТАТУСА ЗАКАЗА
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
    // 4. ЗАГРУЗКА ФАЙЛОВ (УНИВЕРСАЛЬНЫЙ ВАРИАНТ)
    // =========================================================
    const uploadBtn = document.getElementById('uploadFileBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.orderPk;
            
            let fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.multiple = true;
            fileInput.accept = '.pdf,.jpg,.jpeg,.png,.dwg,.dxf,.zip,.doc,.docx,.xls,.xlsx';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);
            
            fileInput.addEventListener('change', function(e) {
                const files = this.files;
                if (!files || files.length === 0) {
                    document.body.removeChild(this);
                    return;
                }
                
                uploadFiles(orderPk, files);
                document.body.removeChild(this);
            });
            
            fileInput.click();
            
            if (navigator.userAgent.toLowerCase().includes('yandex')) {
                console.log('🟡 Yandex Browser detected, using fallback');
                setTimeout(function() {
                    if (!fileInput.files || fileInput.files.length === 0) {
                        fileInput.click();
                    }
                }, 100);
            }
        });
    }

    // Функция загрузки файлов
    function uploadFiles(orderPk, files) {
        const uploadBtn = document.getElementById('uploadFileBtn');
        const originalHtml = uploadBtn.innerHTML;
        
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
        uploadBtn.disabled = true;
        
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        fetch(`/orders/${orderPk}/upload/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
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
                // Ищем карточку с файлами (правую колонку)
                const filesContainer = document.querySelector('.card-body:has(.fa-paperclip)') || 
                                      document.querySelector('.card .card-body');
                
                // Или ищем родителя кнопки загрузки
                const cardBody = uploadBtn.closest('.card-body');
                
                if (cardBody) {
                    const noMsg = cardBody.querySelector('#noFilesMessage');
                    if (noMsg) noMsg.remove();
                    
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
                        // Вставляем перед кнопкой
                        cardBody.insertBefore(fileDiv, uploadBtn);
                    });
                    
                    showToast('Файлы успешно загружены!', 'success');
                } else {
                    showToast('Ошибка: контейнер для файлов не найден', 'danger');
                }
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
    }

    // =========================================================
    // 5. ЗАПУСК ЗАКАЗА ✅ ИСПРАВЛЕНО
    // =========================================================
    const startOrderBtns = document.querySelectorAll('.start-order');
    startOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
            if (confirm(`Запустить заказ ${orderNumber}?`)) {
                // Показываем индикатор загрузки
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
        });
    });

    // =========================================================
    // 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    // =========================================================
    
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

    function showToast(message, type = 'info', duration = 3000) {
        document.querySelectorAll('.custom-toast').forEach(el => el.remove());
        
        const types = {
            success: 'check-circle',
            danger: 'exclamation-circle',
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
        setTimeout(() => toast.classList.add('show'), 50);
        
        toast.querySelector('.toast-close').addEventListener('click', function() {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
        
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        return toast;
    }

    console.log('📦 Заказы загружены');
});