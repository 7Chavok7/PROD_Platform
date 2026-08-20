# orders/templatetag/order_filter | A.Grachev
from django import template

register = template.Library()


@register.filter
def filter_by_status(stages, status):
    """Фильтр: возвращает этапы по статусу"""
    return stages.filter(status=status)


@register.filter
def status_badge_color(status):
    """Фильтр: возвращает цвет бейджа для статуса"""
    colors = {
        'pending': 'secondary',
        'assigned': 'primary',
        'in_progress': 'info',
        'completed': 'success',
        'defect': 'danger',
        'problem': 'warning',
        'on_hold': 'light',
    }
    return colors.get(status, 'secondary')