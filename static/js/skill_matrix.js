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
            // Получаем ФИО из первой ячейки
            const nameCell = row.querySelector('td:first-child');
            const name = nameCell ? nameCell.textContent.toLowerCase() : '';
            
            // Получаем участок из второй ячейки
            const deptCell = row.querySelector('td:nth-child(2)');
            const dept = deptCell ? deptCell.textContent.trim() : '';
            
            let show = true;
            
            // Фильтр по ФИО
            if (searchValue && !name.includes(searchValue)) {
                show = false;
            }
            
            // Фильтр по участку
            if (departmentValue && dept !== departmentValue) {
                show = false;
            }
            
            row.style.display = show ? '' : 'none';
        });
    }
    
    // События
    searchInput.addEventListener('input', filterMatrix);
    departmentFilter.addEventListener('change', filterMatrix);
    
    // Дебаунс для поиска (задержка 300 мс)
    let timeoutId = null;
    searchInput.addEventListener('input', function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(filterMatrix, 300);
    });
    
    // Подсветка строк при наведении
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(13, 110, 253, 0.05)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    console.log('📊 Матрица квалификаций загружена');
});