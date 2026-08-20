/* static/js/stage_detail.js | A.Grachev */
// =========================================================
//   УПРАВЛЕНИЕ ЧЕРТЕЖАМИ В КАРТОЧКЕ ЭТАПА
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    const uploadBtn = document.getElementById('uploadDrawingBtn');
    
    if (!uploadBtn) return;

    // =========================================================
    // 1. ЗАГРУЗКА ЧЕРТЕЖА
    // =========================================================
    uploadBtn.addEventListener('click', function() {
        const stagePk = this.dataset.stagePk;
        const orderPk = this.dataset.orderPk;
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.jpg,.jpeg,.png,.dwg,.dxf';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) {
                document.body.removeChild(this);
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken'));
            
            const originalHtml = uploadBtn.innerHTML;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
            uploadBtn.disabled = true;
            
            fetch(`/orders/${orderPk}/stage/${stagePk}/drawing/upload/`, {
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
                    const container = document.getElementById('drawingsContainer');
                    if (!container) {
                        showToast('Ошибка: контейнер не найден', 'danger');
                        return;
                    }
                    
                    const noMsg = container.querySelector('#noDrawingsMessage');
                    if (noMsg) noMsg.remove();
                    
                    const drawingDiv = document.createElement('div');
                    drawingDiv.className = 'd-flex justify-content-between align-items-center mb-2 drawing-item';
                    drawingDiv.dataset.drawingId = data.drawing.id;
                    drawingDiv.innerHTML = `
                        <div>
                            <i class="fas fa-file me-1"></i>
                            <a href="${data.drawing.url}" target="_blank" class="text-decoration-none">${data.drawing.name}</a>
                            <br>
                            <small class="text-muted">v${data.drawing.version}</small>
                        </div>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary replace-drawing" 
                                    data-drawing-id="${data.drawing.id}"
                                    data-stage-pk="${stagePk}"
                                    data-order-pk="${orderPk}"
                                    title="Заменить чертеж">
                                <i class="fas fa-sync-alt"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-drawing" 
                                    data-drawing-id="${data.drawing.id}"
                                    data-stage-pk="${stagePk}"
                                    data-order-pk="${orderPk}"
                                    title="Удалить чертеж">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    
                    container.insertBefore(drawingDiv, uploadBtn);
                    attachDrawingHandlers();
                    showToast('Чертеж загружен!', 'success');
                } else {
                    showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'danger');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка загрузки чертежа:', error);
                showToast('Ошибка загрузки чертежа', 'danger');
            })
            .finally(() => {
                uploadBtn.innerHTML = originalHtml;
                uploadBtn.disabled = false;
                document.body.removeChild(this);
            });
        });
        
        fileInput.click();
    });

    // =========================================================
    // 2. УДАЛЕНИЕ ЧЕРТЕЖА (AJAX)
    // =========================================================
    function handleDeleteDrawing(e) {
        e.stopPropagation();
        const drawingId = this.dataset.drawingId;
        const stagePk = this.dataset.stagePk;
        const orderPk = this.dataset.orderPk;
        
        if (!confirm('Удалить этот чертеж?')) return;
        
        fetch(`/orders/${orderPk}/stage/${stagePk}/drawing/${drawingId}/delete-ajax/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const item = document.querySelector(`.drawing-item[data-drawing-id="${drawingId}"]`);
                if (item) {
                    item.remove();
                    const container = document.getElementById('drawingsContainer');
                    const remaining = container.querySelectorAll('.drawing-item');
                    if (remaining.length === 0) {
                        const noMsg = container.querySelector('#noDrawingsMessage');
                        if (!noMsg) {
                            const msg = document.createElement('p');
                            msg.className = 'text-muted small';
                            msg.id = 'noDrawingsMessage';
                            msg.textContent = 'Чертежи не загружены';
                            container.insertBefore(msg, uploadBtn);
                        }
                    }
                }
                showToast('Чертеж удален', 'success');
            } else {
                showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'danger');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка удаления чертежа:', error);
            showToast('Ошибка удаления чертежа', 'danger');
        });
    }

    // =========================================================
    // 3. ЗАМЕНА ЧЕРТЕЖА (AJAX)
    // =========================================================
    function handleReplaceDrawing(e) {
        e.stopPropagation();
        const drawingId = this.dataset.drawingId;
        const stagePk = this.dataset.stagePk;
        const orderPk = this.dataset.orderPk;
        const btn = this;
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.jpg,.jpeg,.png,.dwg,.dxf';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        fileInput.addEventListener('change', function() {
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
            
            fetch(`/orders/${orderPk}/stage/${stagePk}/drawing/${drawingId}/replace/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const item = document.querySelector(`.drawing-item[data-drawing-id="${drawingId}"]`);
                    if (item) {
                        const info = item.querySelector('div:first-child');
                        info.innerHTML = `
                            <i class="fas fa-file me-1"></i>
                            <a href="${data.drawing.url}" target="_blank" class="text-decoration-none">${data.drawing.name}</a>
                            <br>
                            <small class="text-muted">v${data.drawing.version}</small>
                        `;
                        item.dataset.drawingId = data.drawing.id;
                        const buttons = item.querySelectorAll('.btn');
                        buttons.forEach(b => {
                            b.dataset.drawingId = data.drawing.id;
                        });
                    }
                    showToast(`Чертеж заменен (v${data.drawing.version})`, 'success');
                } else {
                    showToast('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'danger');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка замены чертежа:', error);
                showToast('Ошибка замены чертежа', 'danger');
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
    // 4. ПРИВЯЗКА ОБРАБОТЧИКОВ
    // =========================================================
    function attachDrawingHandlers() {
        document.querySelectorAll('.delete-drawing').forEach(function(btn) {
            btn.removeEventListener('click', handleDeleteDrawing);
            btn.addEventListener('click', handleDeleteDrawing);
        });
        
        document.querySelectorAll('.replace-drawing').forEach(function(btn) {
            btn.removeEventListener('click', handleReplaceDrawing);
            btn.addEventListener('click', handleReplaceDrawing);
        });
    }

    // =========================================================
    // 5. ИНИЦИАЛИЗАЦИЯ
    // =========================================================
    attachDrawingHandlers();

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
});