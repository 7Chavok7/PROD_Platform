# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Заказы
    path('', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('<int:pk>/restore/', views.order_restore, name='order_restore'),
    path('<int:pk>/upload/', views.order_upload_files, name='order_upload_files'),
    path('<int:pk>/start/', views.order_start, name='order_start'),
    
    # Заказ
    path('<int:pk>/file/<int:file_pk>/delete/', views.order_file_delete, name='order_file_delete'),
    path('<int:pk>/file/<int:file_pk>/replace/', views.order_file_replace, name='order_file_replace'),
    
    # Этапы
    path('<int:order_pk>/stage/create/', views.stage_create, name='stage_create'),
    path('<int:order_pk>/stage/<int:pk>/', views.stage_detail, name='stage_detail'),
    path('<int:order_pk>/stage/<int:pk>/edit/', views.stage_edit, name='stage_edit'),
    path('<int:order_pk>/stage/<int:pk>/delete/', views.stage_delete, name='stage_delete'),
    
    # Чертежи
    path('<int:order_pk>/stage/<int:stage_pk>/drawing/create/', views.drawing_create, name='drawing_create'),
    path('<int:order_pk>/stage/<int:stage_pk>/drawing/<int:pk>/delete/', views.drawing_delete, name='drawing_delete'),
    path('<int:order_pk>/stage/<int:stage_pk>/drawing/upload/', views.stage_upload_drawing, name='stage_upload_drawing'),
    path('<int:order_pk>/stage/<int:stage_pk>/drawing/<int:pk>/replace/', views.drawing_replace, name='drawing_replace'),
    path('<int:order_pk>/stage/<int:stage_pk>/drawing/<int:pk>/delete-ajax/', views.drawing_delete_ajax, name='drawing_delete_ajax'),
    
    # Личный кабинет сотрудника
    path('my-tasks/', views.employee_tasks, name='employee_tasks'),
    
    # Действия сотрудника над этапом
    path('stage/<int:pk>/start/', views.stage_start, name='stage_start'),
    path('stage/<int:pk>/complete/', views.stage_complete, name='stage_complete'),
    path('stage/<int:pk>/defect/', views.stage_defect, name='stage_defect'),
    path('stage/<int:pk>/problem/', views.stage_problem, name='stage_problem'),
    
    # Дашборд
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    
    # Отчеты
    path('reports/customer-orders/', views.customer_orders_report, name='customer_orders_report'),
    path('reports/customer-reliability/', views.customer_reliability_report, name='customer_reliability_report'),
    path('reports/customer/<int:pk>/', views.customer_detail_report, name='customer_detail_report'),
]