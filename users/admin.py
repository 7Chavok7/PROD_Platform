# .users/admin.py | A.Grachev
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Кастомная админка для модели User с добавлением роли
    """
    list_display = ['username', 'email', 'first_name', 'last_name','is_active']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    
    # Добавляем поле role в редактирование
    fieldsets = UserAdmin.fieldsets + (
        ('Роли и права', {
            'fields': ('role',),
        }),
    )
    
    # Добавляем поле role при создании
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Роли и права', {
            'fields': ('role',),
        }),
    )

# Register your models here.
