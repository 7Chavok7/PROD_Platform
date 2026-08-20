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
                const filesContainer = document.getElementById('filesContainer');
                
                if (filesContainer) {
                    const noMsg = filesContainer.querySelector('#noFilesMessage');
                    if (noMsg) noMsg.remove();
                    
                     data.files.forEach(function(file) {
                        const fileDiv = document.createElement('div');
                        fileDiv.className = 'd-flex justify-content-between align-items-center mb-2 file-item';
                        fileDiv.dataset.fileId = file.id;
                        fileDiv.innerHTML = `
                            <div>
                                <i class="fas fa-file me-1"></i>
                                <a href="${file.url}" target="_blank" class="text-decoration-none">${file.name}</a>
                                <br>
                                <small class="text-muted">
                                    ${file.type}  
                                    ${file.version > 1 ? `<span class="badge bg-secondary">v${file.version}</span>` : ''}
                                </small>
                            </div>
                            <div class="d-flex gap-1">
                                <button class="btn btn-sm btn-outline-primary replace-file" 
                                        data-file-id="${file.id}"
                                        data-order-pk="${orderPk}"
                                        title="Заменить файл">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger delete-file" 
                                        data-file-id="${file.id}"
                                        data-order-pk="${orderPk}"
                                        title="Удалить файл">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        `;
                        filesContainer.appendChild(fileDiv);
                    });
                    
                    // Добавляем обработчики для новых кнопок
                    attachFileHandlers();
                    
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
    // 5. ЗАПУСК ЗАКАЗА
    // =========================================================
    const startOrderBtns = document.querySelectorAll('.start-order');
    startOrderBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const orderPk = this.dataset.pk;
            const orderNumber = this.dataset.number || 'заказ';
            
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
        });
    });

    // =========================================================
    // 6. УДАЛЕНИЕ ФАЙЛА
    // =========================================================
    function handleDeleteFile(e) {
        e.stopPropagation();
        const fileId = this.dataset.fileId;
        const orderPk = this.dataset.orderPk;
        
        if (!confirm('Удалить этот файл?')) return;
        
        // ПРАВИЛЬНЫЙ URL
        fetch(`/orders/${orderPk}/file/${fileId}/delete/`, {
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
                const fileItem = document.querySelector(`.file-item[data-file-id="${fileId}"]`);
                if (fileItem) {
                    fileItem.remove();
                    const remaining = document.querySelectorAll('.file-item');
                    const noMsg = document.getElementById('noFilesMessage');
                    if (remaining.length === 0 && !noMsg) {
                        const container = document.getElementById('filesContainer');
                        const msg = document.createElement('p');
                        msg.className = 'text-muted small';
                        msg.id = 'noFilesMessage';
                        msg.textContent = 'Файлы не загружены';
                        container.appendChild(msg);
                    }
                }
                showToast('Файл успешно удален', 'success');
            } else {
                showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'danger');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка удаления файла:', error);
            showToast('Ошибка удаления файла', 'danger');
        });
    }

    // =========================================================
    // 7. ЗАМЕНА ФАЙЛА
    // =========================================================
    function handleReplaceFile(e) {
        e.stopPropagation();
        const fileId = this.dataset.fileId;
        const orderPk = this.dataset.orderPk;
        const btn = this;
        
        if (!fileId || isNaN(fileId)) {
            showToast('Ошибка: некорректный ID файла', 'danger');
            return;
        }
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.jpg,.jpeg,.png,.dwg,.dxf,.zip,.doc,.docx,.xls,.xlsx';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        fileInput.addEventListener('change', function(e) {
            const file = this.files[0];
            if (!file) {
                document.body.removeChild(this);
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
            
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            btn.disabled = true;
            
            fetch(`/orders/${orderPk}/file/${fileId}/replace/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
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
                    // Находим элемент старого файла и заменяем его содержимое
                    const fileItem = document.querySelector(`.file-item[data-file-id="${fileId}"]`);
                    if (fileItem) {
                        // Обновляем содержимое
                        const fileInfo = fileItem.querySelector('div:first-child');
                        fileInfo.innerHTML = `
                            <i class="fas fa-file me-1"></i>
                            <a href="${data.file.url}" target="_blank" class="text-decoration-none">${data.file.name}</a>
                            <br>
                            <small class="text-muted">
                                ${data.file.type}
                                ${data.file.version > 1 ? `<span class="badge bg-secondary">v${data.file.version}</span>` : ''}
                            </small>
                        `;
                        // Обновляем ID файла
                        fileItem.dataset.fileId = data.file.id;
                        const buttons = fileItem.querySelectorAll('.btn');
                        buttons.forEach(b => {
                            b.dataset.fileId = data.file.id;
                        });
                    }
                    showToast(`Файл успешно заменен (v${data.file.version})`, 'success');
                } else {
                    showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'danger');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка замены файла:', error);
                showToast('Ошибка замены файла', 'danger');
            })
            .finally(() => {
                btn.innerHTML = originalHtml;
                btn.disabled = false;
                document.body.removeChild(this);
            });
        });
        
        fileInput.click();
    }

    // =========================================================
    // 8. ПРИВЯЗКА ОБРАБОТЧИКОВ ДЛЯ ФАЙЛОВ
    // =========================================================
    function attachFileHandlers() {
        // Удаление файла
        document.querySelectorAll('.delete-file').forEach(function(btn) {
            btn.removeEventListener('click', handleDeleteFile);
            btn.addEventListener('click', handleDeleteFile);
        });
        
        // Замена файла
        document.querySelectorAll('.replace-file').forEach(function(btn) {
            btn.removeEventListener('click', handleReplaceFile);
            btn.addEventListener('click', handleReplaceFile);
        });
    }

    // =========================================================
    // 9. ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ ФАЙЛОВ
    // =========================================================
    attachFileHandlers();

    // =========================================================
    // 10. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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