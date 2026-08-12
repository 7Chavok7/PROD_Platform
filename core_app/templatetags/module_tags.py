# core_app/templatetags/module_tags.py | A.Grachev
from django import template
from django.apps import apps


register = template.Library()

@register.filter
def module_active(module_name):
    """
    Проверяет, активен ли модуль.
    Использование: {% if 'employees'|ismodule_active %}
    """
    return apps.is_installed(module_name)
