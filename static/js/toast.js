/* static/js/toast.js | A.Grachev */
// Глобальный менеджер уведомлений
const ToastManager = {
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        const types = {
            success: 'check-circle',
            danger: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = `
            top: 80px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
    },
    
    success(message) { return this.show(message, 'success'); },
    error(message) { return this.show(message, 'danger'); },
    warning(message) { return this.show(message, 'warning'); },
    info(message) { return this.show(message, 'info'); }
};

// Делаем глобальным
window.ToastManager = ToastManager;