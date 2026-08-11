document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    const searchInput = document.getElementById('filterSearch');
    const filterSelect = document.getElementById('filterSelect');
    const filterStatus = document.getElementById('filterStatus');
    const filterPriority = document.getElementById('filterPriority');
    const table = document.getElementById('filterTable');
    
    if (!table) {
        console.log('❌ Таблица не найдена');
        return;
    }
    
    const rows = table.querySelectorAll('tbody tr');
    let timeoutId = null;

    console.log('✅ Фильтр загружен, строк:', rows.length);

    function filterRows() {
        const searchValue = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectValue = filterSelect ? filterSelect.value : '';
        const statusValue = filterStatus ? filterStatus.value : '';
        const priorityValue = filterPriority ? filterPriority.value : '';

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let rowText = '';
            cells.forEach(cell => {
                rowText += cell.textContent.toLowerCase() + ' ';
            });

            let show = true;
            
            // Поиск
            if (searchValue && !rowText.includes(searchValue)) {
                show = false;
            }

            // Фильтр по участку (индекс 2)
            if (selectValue && cells.length > 2) {
                const deptText = cells[2] ? cells[2].textContent.trim() : '';
                if (deptText !== selectValue) {
                    show = false;
                }
            }

            // Фильтр по статусу (индекс 4)
            if (statusValue && cells.length > 4) {
                const statusText = cells[4] ? cells[4].textContent.trim() : '';
                if (statusText !== statusValue) {
                    show = false;
                }
            }

            // Фильтр по приоритету (в карточке заказа — ищем в тексте)
            if (priorityValue) {
                const priorityText = row.querySelector('.badge-priority');
                if (priorityText && priorityText.textContent.trim() !== priorityValue) {
                    show = false;
                }
            }

            row.style.display = show ? '' : 'none';
        });
    }

    // События
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(filterRows, 300);
        });
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', filterRows);
    }
    if (filterStatus) {
        filterStatus.addEventListener('change', filterRows);
    }
    if (filterPriority) {
        filterPriority.addEventListener('change', filterRows);
    }
    
    // Первый запуск
    filterRows();
});