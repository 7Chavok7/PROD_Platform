# .employee/admin.py | A.Grachev
from django.contrib import admin
from .models import (
    Department,
    Employee,
    Position,
    Skill,
    EmployeeSkill
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'head'
    ]
    search_fields = [
        'name',
        'code'
    ]

    
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category'
    ]
    search_fields = [
        'name'
    ]
    

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code'
    ]
    search_fields = [
        'name',
        'code'
    ]

class EmployeeSkillInline(admin.TabularInline):
    model = EmployeeSkill
    extra = 1
    autocomplete_fields = ['skill']
    verbose_name_plural = 'Навыки сотрудника'
    

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'short_name_display',
        'personal_number',
        'department',
        'position',
        'status'
    ]
    list_filter = [
        'department',
        'status'
    ]
    search_fields = [
        'last_name',
        'personal_number'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    inlines = [EmployeeSkillInline]
    fieldsets = (
        ('Персональные данные', {
            'fields': (
                'user', 
                'last_name',
                'first_name',
                'patronymic',
            )
        }),
        ('Контакты', {
            'fields': (
                'phone',
                'email'
            ),
            'classes': ('collapse',)
        }),
        ('Данные о сотруднике', {
            'fields': (
                'personal_number', 
                (
                    'department',
                    'position'
                ),
                (
                    'hire_date',
                    'status',
                ),
            )
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_name_display(self, obj):
        return obj.short_name()
    short_name_display.short_description = 'ФИО'