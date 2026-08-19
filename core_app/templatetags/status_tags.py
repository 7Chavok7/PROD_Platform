# core_app/templatetags/status_tags.py
from django import template

register = template.Library()

@register.filter
def status_badge_color(status):
    """Единый фильтр для статусов"""
    colors = {
        # Статусы заказов
        'draft': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger',
        'on_hold': 'warning',
        
        # Статусы этапов
        'pending': 'secondary',
        'assigned': 'primary',
        'defect': 'danger',
        'problem': 'warning',
    }
    return colors.get(status, 'secondary')