/* static/js/skill_matrix.js | A.Grachev */
// Матрица квалификаций — фильтрация и интерактивность
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    const searchInput = document.getElementById('matrixSearch');
    const departmentFilter = document.getElementById('departmentFilter');
    const rows = document.querySelectorAll('tbody tr');
    
    if (!searchInput || !departmentFilter || !rows.length) {
        return;
    }
    
    function filterMatrix() {
        const searchValue = searchInput.value.toLowerCase().trim();
        const departmentValue = departmentFilter.value;
        
        rows.forEach(row => {
            const nameCell = row.querySelector('td:first-child');
            const name = nameCell ? nameCell.textContent.toLowerCase() : '';
            
            const deptCell = row.querySelector('td:nth-child(2)');
            const dept = deptCell ? deptCell.textContent.trim() : '';
            
            let show = true;
            
            if (searchValue && !name.includes(searchValue)) {
                show = false;
            }
            
            if (departmentValue && dept !== departmentValue) {
                show = false;
            }
            
            row.style.display = show ? '' : 'none';
        });
    }
    
    let timeoutId = null;
    searchInput.addEventListener('input', function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(filterMatrix, 300);
    });
    
    departmentFilter.addEventListener('change', filterMatrix);
    
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(13, 110, 253, 0.05)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Добавляем подсказки для заголовков
    document.querySelectorAll('.matrix-table thead th[title]').forEach(function(th) {
        const fullName = th.getAttribute('title');
        if (fullName) {
            th.setAttribute('data-bs-toggle', 'tooltip');
            th.setAttribute('data-bs-placement', 'top');
            th.setAttribute('data-bs-title', fullName);
        }
    });
    
    // Инициализируем тултипы
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(el) {
            return new bootstrap.Tooltip(el);
        });
    }
    
    console.log('📊 Матрица квалификаций загружена');
});