# core_app/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получение значения из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_item_from_request(request, key):
    """Получение GET-параметра из запроса"""
    if request is None:
        return None
    return request.GET.get(key, '')


@register.filter
def multiply(value, arg):
    """Умножение: value * arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Деление: value / arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Вычитание: value - arg"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def add_days(value, days):
    """Добавление дней к дате"""
    from datetime import timedelta
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError, AttributeError):
        return value


@register.filter
def status_badge_color(status):
    """Цвет бейджа для статуса заказа"""
    colors = {
        'draft': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger',
        'on_hold': 'warning',
        'pending': 'secondary',
        'assigned': 'primary',
        'defect': 'danger',
        'problem': 'warning',
    }
    return colors.get(status, 'secondary')


@register.filter
def order_status_badge(status):
    """Цвет бейджа для статуса заказа"""
    colors = {
        'draft': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger',
        'on_hold': 'warning',
    }
    return colors.get(status, 'secondary')