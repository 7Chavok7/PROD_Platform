# employees/templatetags/custom_filters.py | A.Grachev
from django import template


register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получаем значение из словаря по ключу"""
    return dictionary.get(key)