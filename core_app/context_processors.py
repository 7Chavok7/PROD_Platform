# core_app/context_processors.py | A.Grachev
from django.apps import apps


def active_modules(request):
    """Добавляет в контекст шаблонов флаги активности модулей"""
    return {
        'has_employees': apps.is_installed('employees'),
        'has_customers': apps.is_installed('customers'),
        'has_warehouse': apps.is_installed('warehouse'),
        'has_logistics': apps.is_installed('logistics'),
    }