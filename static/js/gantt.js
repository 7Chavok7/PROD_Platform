/* static/js/gantt.js | A.Grachev */
// =========================================================
//   ГАНТ-ДИАГРАММА
// =========================================================

class GanttChart {
    constructor(elementId, tasks, options = {}) {
        this.elementId = elementId;
        this.tasks = tasks;
        this.options = {
            on_click: options.on_click || null,
            on_date_change: options.on_date_change || null,
            on_progress_change: options.on_progress_change || null,
            on_view_change: options.on_view_change || null,
            view_mode: options.view_mode || 'Week',
            language: 'ru',
            ...options
        };
        this.chart = null;
        this.init();
    }

    init() {
        const container = document.getElementById(this.elementId);
        if (!container) {
            console.warn(`Gantt container #${this.elementId} not found`);
            return;
        }

        if (this.tasks.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-chart-bar fa-3x d-block mb-3 opacity-25"></i>
                    <h6>Нет данных для отображения</h6>
                    <p class="small">Добавьте этапы с указанием дат</p>
                </div>
            `;
            return;
        }

        // Фильтруем задачи с датами
        const validTasks = this.tasks.filter(task => task.start && task.end);
        
        if (validTasks.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-calendar-times fa-3x d-block mb-3 opacity-25"></i>
                    <h6>Нет этапов с указанными датами</h6>
                    <p class="small">Укажите плановые даты для этапов</p>
                </div>
            `;
            return;
        }

        try {
            this.chart = new Gantt(this.elementId, validTasks, this.options);
        } catch (error) {
            console.error('Gantt chart error:', error);
            container.innerHTML = `
                <div class="text-center py-5 text-danger">
                    <i class="fas fa-exclamation-triangle fa-3x d-block mb-3"></i>
                    <h6>Ошибка загрузки диаграммы</h6>
                    <p class="small">${error.message}</p>
                </div>
            `;
        }
    }

    refresh(tasks) {
        if (tasks) {
            this.tasks = tasks;
        }
        this.init();
    }

    changeView(mode) {
        if (this.chart) {
            this.chart.change_view_mode(mode);
        }
    }
}