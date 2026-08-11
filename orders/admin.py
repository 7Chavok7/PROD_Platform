# orders/admin.py | A.Grachev
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Order, OrderFile, Stage, Drawing


@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin):
    list_display = ['number', 'name', 'customer', 'status', 'priority', 'planned_completion_date']
    list_filter = ['status', 'priority']
    search_fields = ['number', 'name', 'customer__name']
    readonly_fields = ['number', 'created_at', 'updated_at']


@admin.register(OrderFile)
class OrderFileAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'file_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type']
    search_fields = ['name']


@admin.register(Stage)
class StageAdmin(SimpleHistoryAdmin):
    list_display = ['order', 'number', 'name', 'status', 'assigned_employee', 'planned_start_date', 'planned_finish_date']
    list_filter = ['status', 'department']
    search_fields = ['order__number', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Drawing)
class DrawingAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'version', 'uploaded_by', 'uploaded_at']
    list_filter = ['stage__order']
    search_fields = ['name']