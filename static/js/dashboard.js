/* static/js/dashboard.js | A.Grachev */
// =========================================================
//   DASHBOARD - ИНТЕРАКТИВНОСТЬ ДАШБОРДА
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // =========================================================
    // 1. ИНИЦИАЛИЗАЦИЯ ГРАФИКОВ
    // =========================================================
    function initCharts() {
        // Проверяем, есть ли данные для графиков
        const hasStatusData = typeof statusData !== 'undefined' && statusData.length > 0;
        const hasDailyData = typeof dailyLabels !== 'undefined' && dailyLabels.length > 0;
        
        // =========================================================
        // КРУГОВАЯ ДИАГРАММА (СТАТУСЫ)
        // =========================================================
        if (hasStatusData) {
            const statusCtx = document.getElementById('statusChart');
            if (statusCtx) {
                new Chart(statusCtx.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: statusData.map(item => item.label),
                        datasets: [{
                            data: statusData.map(item => item.value),
                            backgroundColor: statusData.map(item => item.color),
                            borderWidth: 3,
                            borderColor: '#fff',
                            hoverOffset: 10
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 20,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    font: {
                                        size: 12,
                                        weight: '500'
                                    }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        },
                        cutout: '65%'
                    }
                });
            }
        }
        
        // =========================================================
        // ГРАФИК ДИНАМИКИ (ПО ДНЯМ)
        // =========================================================
        if (hasDailyData) {
            const dailyCtx = document.getElementById('dailyChart');
            if (dailyCtx) {
                new Chart(dailyCtx.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: dailyLabels,
                        datasets: [{
                            label: 'Заказов',
                            data: dailyValues,
                            backgroundColor: 'rgba(13, 110, 253, 0.7)',
                            borderColor: '#0d6efd',
                            borderWidth: 2,
                            borderRadius: 6,
                            barPercentage: 0.6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.parsed.y} заказов`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1,
                                    precision: 0,
                                    font: {
                                        size: 11
                                    }
                                },
                                grid: {
                                    color: 'rgba(0,0,0,0.05)'
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    font: {
                                        size: 10
                                    },
                                    maxTicksLimit: 15
                                }
                            }
                        }
                    }
                });
            }
        }
    }

    // =========================================================
    // 2. АВТООБНОВЛЕНИЕ ДАННЫХ (КАЖДЫЕ 30 СЕКУНД)
    // =========================================================
    function setupAutoRefresh() {
        const refreshBtn = document.querySelector('[onclick*="window.location.reload"]');
        if (refreshBtn) {
            // Удаляем обработчик из HTML
            refreshBtn.removeAttribute('onclick');
            refreshBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const icon = this.querySelector('.fa-sync-alt');
                if (icon) {
                    icon.classList.add('fa-spin');
                }
                this.disabled = true;
                
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            });
        }
    }

    // =========================================================
    // 3. АНИМАЦИЯ ПРОГРЕСС-БАРОВ ПРИ ЗАГРУЗКЕ
    // =========================================================
    function animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-mini .progress-bar');
        progressBars.forEach(function(bar) {
            const targetWidth = bar.style.width;
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = targetWidth;
            }, 100);
        });
    }

    // =========================================================
    // 4. ИНИЦИАЛИЗАЦИЯ
    // =========================================================
    
    // Ждем загрузки Chart.js
    if (typeof Chart !== 'undefined') {
        initCharts();
    } else {
        // Если Chart.js еще не загружен, ждем
        const checkChart = setInterval(function() {
            if (typeof Chart !== 'undefined') {
                clearInterval(checkChart);
                initCharts();
            }
        }, 100);
    }
    
    setupAutoRefresh();
    animateProgressBars();
    
    console.log('📊 Дашборд загружен');
});