# customers/admin.py | A.Grachev
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(SimpleHistoryAdmin):
    list_display = [
        'name',
        'short_name',
        'type',
        'inn',
        'contact_person',
        'phone',
        'is_active'
    ]
    list_filter = [
        'type',
        'is_active'
    ]
    search_fields = [
        'name',
        'short_name',
        'inn',
        'contact_person'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'short_name',
                'type',
                'inn',
                'kpp',
                'ogrn'
            )
        }),
        ('Контакты', {
            'fields': (
                'contact_person',
                'phone',
                'email',
                'address',
                'actual_address'
            )
        }),
        ('Банковские реквизиты', {
            'fields': (
                'bank_name',
                'bik',
                'checking_account',
                'cor_account'
            )
        }),
        ('Дополнительно', {
            'fields': (
                'comment',
                'is_active'
            )
        }),
        ('Метаданные', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': (
                'collapse',
            )
        })
    )
