import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from django.http import JsonResponse
from .models import (
    Order, 
    Stage, 
    Drawing, 
    OrderFile)
from .forms import (
    OrderForm, 
    StageForm, 
    DrawingForm, 
    OrderFileForm)
from .services import OrderProgressService
from employees.models import Employee


def is_manager(user):
    if user.is_superuser:
        return True
    return user.is_authenticated and user.role in ['admin', 'director', 'manager']

# =========================================================
# =                     DASHBOARD                         =
# =========================================================
@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    """
    Dashboard для менеджера.
    Режимы: minimal (базовый) и advanced (с графиками)
    """
    
    # Проверяем пользователя, если сотрудник, то редирект на его задачи
    if hasattr(request.user, 'employee') and request.user.employee:
        access_level = request.user.employee.get_access_level()
        if access_level == 'employee':
            return redirect('orders:employee_tasks')
        
    # Получаем режим из GET-запроса
    mode = request.GET.get('mode', 'minimal')
    
    # --- ФИЛЬТРЫ ---# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from .models import (
    Order, 
    Stage, 
    Drawing, 
    OrderFile)
from .forms import (
    OrderForm, 
    StageForm, 
    DrawingForm, 
    OrderFileForm)
from .services import OrderProgressService
from employees.models import Employee


def is_manager(user):
    if user.is_superuser:
        return True
    return user.is_authenticated and user.role in ['admin', 'director', 'manager']

# =========================================================
# =                     DASHBOARD                         =
# =========================================================
@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    """
    Dashboard для менеджера.
    Режимы: minimal (базовый) и advanced (с графиками)
    """
    
    # Проверяем пользователя, если сотрудник, то редирект на его задачи
    if hasattr(request.user, 'employee') and request.user.employee:
        access_level = request.user.employee.get_access_level()
        if access_level == 'employee':
            return redirect('orders:employee_tasks')
        
    # Получаем режим из GET-запроса
    mode = request.GET.get('mode', 'minimal')
    
    # --- ФИЛЬТРЫ ---
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # --- БАЗОВЫЙ ЗАПРОС ---
    # Для директора, админа или суперпользователя - все заказы
    if request.user.is_superuser or request.user.role in ['admin', 'director']:
        orders = Order.objects.all()
    else:
        # Менеджер - только свои заказы
        orders = Order.objects.filter(responsible_manager=request.user)
        
    # Применяем фильтры
    if status_filter:
        orders = orders.filter(status=status_filter)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
        
    # --- СТАТИСТИКА ---
    total_orders = orders.count()
    in_progress = orders.filter(status=Order.Status.IN_PROGRESS).count()
    completed = orders.filter(status=Order.Status.COMPLETED).count()
    cancelled = orders.filter(status=Order.Status.CANCELLED).count()
    draft = orders.filter(status=Order.Status.DRAFT).count()
    
    # Просроченные заказы
    overdue = orders.filter(
        status=Order.Status.IN_PROGRESS,
        planned_completion_date__lt=timezone.now().date()
    ).count()
    
    # Процент выполнения
    completion_rate = int((completed / total_orders * 100)) if total_orders > 0 else 0
    
    # --- АКТИВНЫЕ ЗАКАЗЫ (для таблицы) ---
    active_orders = orders.filter(
        status__in=[Order.Status.IN_PROGRESS, Order.Status.DRAFT]
    ).select_related('responsible_manager').prefetch_related('stages')
    
    gantt_data = []
    for order in active_orders:
        for stage in order.stages.all().order_by('number'):
            status_colors = {
                'pending': '#6c757d',
                'assigned': '#0d6efd',
                'in_progress': '#0dcaf0',
                'completed': '#198754',
                'defect': '#dc3545',
                'problem': '#ffc107',
                'on_hold': '#fd7e14',
            }
            gantt_data.append({
                'id': f'order-{order.id}-stage-{stage.id}',
                'name': f'{order.number}: {stage.name}',
                'start': stage.planned_start_date.strftime('%Y-%m-%d') if stage.planned_start_date else None,
                'end': stage.planned_finish_date.strftime('%Y-%m-%d') if stage.planned_finish_date else None,
                'progress': 100 if stage.status == 'completed' else 0,
                'custom_class': stage.status,
                'color': status_colors.get(stage.status, '#6c757d'),
            })
    
    # Добавляем прогресс для каждого заказа
    for order in active_orders:
        total_stages = order.stages.count()
        completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
        order.progress = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0
        order.completed_count = completed_stages
        order.is_overdue = (
            order.status == Order.Status.IN_PROGRESS and
            order.planned_completion_date and
            order.planned_completion_date < timezone.now().date()
        )
    
    # --- ДАННЫЕ ДЛЯ ГРАФИКОВ (ПРОДВИНУТЫЙ РЕЖИМ) ---
    
    # 1. Статусы для круговой диаграммы
    status_data = []
    status_colors = {
        'draft': '#6c757d',
        'in_progress': '#0d6efd',
        'completed': '#198754',
        'cancelled': '#dc3545',
    }
    for status_code, status_label in Order.Status.choices:
        count = orders.filter(status=status_code).count()
        if count > 0:
            status_data.append({
                'label': status_label,
                'value': count,
                'color': status_colors.get(status_code, '#6c757d')
            })
    
    # 2. Динамика заказов по дням (последние 30 дней)
    today = timezone.now().date()
    days_ago = 30
    
    daily_stats = orders.filter(
        created_at__date__gte=today - timedelta(days=days_ago)
    ).extra(
        {'day': 'date(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Заполняем массив для всех дней
    daily_labels = []
    daily_values = []
    for i in range(days_ago):
        day = today - timedelta(days=days_ago - i - 1)
        daily_labels.append(day.strftime('%d.%m'))
        daily_values.append(0)
    
    for stat in daily_stats:
        day_str = stat['day'].strftime('%d.%m')
        if day_str in daily_labels:
            idx = daily_labels.index(day_str)
            daily_values[idx] = stat['count']
    
    # 3. Загрузка сотрудников (если модуль employees активен)
    employee_load = []
    if apps.is_installed('employees'):
        from employees.models import Employee
        employees = Employee.objects.filter(status='active').select_related('user')[:10]
        for emp in employees:
            active = Stage.objects.filter(
                assigned_employee=emp,
                status__in=[Stage.Status.ASSIGNED, Stage.Status.IN_PROGRESS]
            ).count()
            in_work = Stage.objects.filter(
                assigned_employee=emp,
                status=Stage.Status.IN_PROGRESS
            ).count()
            employee_load.append({
                'name': emp.full_name,
                'active': active,
                'in_work': in_work,
                'load': active * 2  # Условная загрузка (1 задача = 2 часа)
            })
    
    # 4. Загрузка участков (для директора)
    department_load = []
    if apps.is_installed('employees') and request.user.role in ['director', 'admin']:
        from employees.models import Department
        departments = Department.objects.all()
        for dept in departments:
            active_stages = Stage.objects.filter(
                department=dept,
                status__in=[Stage.Status.IN_PROGRESS, Stage.Status.ASSIGNED]
            ).count()
            total_stages = Stage.objects.filter(department=dept).count()
            load_percent = int((active_stages / total_stages * 100)) if total_stages > 0 else 0
            department_load.append({
                'name': dept.name,
                'active': active_stages,
                'total': total_stages,
                'load': load_percent
            })
    
    # 5. Топ-менеджеры (для директора)
    top_managers = []
    if request.user.role in ['director', 'admin']:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        top_managers = User.objects.filter(
            managed_orders__isnull=False
        ).annotate(
            order_count=Count('managed_orders')
        ).order_by('-order_count')[:5]
    
    context = {
        'mode': mode,
        'total_orders': total_orders,
        'in_progress': in_progress,
        'completed': completed,
        'cancelled': cancelled,
        'draft': draft,
        'overdue': overdue,
        'completion_rate': completion_rate,
        'active_orders': active_orders,
        'gantt_data': json.dumps(gantt_data),    # Передаем в JSON
        'status_data': status_data,
        'daily_labels': daily_labels,
        'daily_values': daily_values,
        'employee_load': employee_load,
        'department_load': department_load,
        'top_managers': top_managers,
        'active_menu': 'dashboard',
        'title': 'Дашборд',
        # Для отображения в шаблоне
        'is_manager': request.user.role == 'manager' and not request.user.is_superuser,
        'show_all_orders': request.user.is_superuser or request.user.role in ['admin', 'director'],
    }
    
    return render(request, 'orders/manager_dashboard.html', context)
    
       

# =========================================================
# =                   ЗАКАЗЫ (CRUD)                       =
# =========================================================

@login_required
@user_passes_test(is_manager)
def order_list(request):
    """Список заказов с фильтрацией"""
    orders = Order.objects.select_related('customer', 'responsible_manager').prefetch_related('stages').all()
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Фильтр по приоритету
    priority = request.GET.get('priority')
    if priority:
        orders = orders.filter(priority=priority)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(number__icontains=search) |
            Q(name__icontains=search) |
            Q(customer__name__icontains=search)
        )
    
    # Добавляем прогресс через сервис
    orders = OrderProgressService.get_orders_with_progress(orders)
    
    context = {
        'orders': orders,
        'statuses': Order.Status.choices,
        'active_menu': 'orders',
        'title': 'Заказы',
    }
    return render(request, 'orders/order_list.html', context)


@login_required
@user_passes_test(is_manager)
def order_detail(request, pk):
    """Детальная страница заказа"""
    order = get_object_or_404(Order.objects.prefetch_related('stages', 'files'), pk=pk)
    
    # Используем сервис для расчёта
    progress = OrderProgressService.get_progress_percent(order)
    completed_count = OrderProgressService.get_completed_stages_count(order)
    
    context = {
        'order': order,
        'progress': progress,
        'completed_count': completed_count,
        'active_menu': 'orders',
        'title': f'{order.number} — {order.name}',
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@user_passes_test(is_manager)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        
        # ✅ ОТЛАДКА: выводим ошибки формы
        if not form.is_valid():
            print("❌ ФОРМА НЕ ВАЛИДНА!")
            print(form.errors)
            print(form.cleaned_data)
        else:
            print("✅ ФОРМА ВАЛИДНА")
            print(form.cleaned_data)
        
        if form.is_valid():
            order = form.save(commit=False)
            order.save()
            form.save_m2m()
            messages.success(request, f'Заказ {order.number} успешно создан!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'title': 'Создание заказа',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_form.html', context)


@login_required
@user_passes_test(is_manager)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Заказ {order.number} успешно обновлён!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'Редактирование заказа {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_form.html', context)


@login_required
@user_passes_test(is_manager)
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, f'Заказ {order.number} удалён!')
        return redirect('orders:order_list')
    
    context = {
        'order': order,
        'title': f'Удаление заказа {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_confirm_delete.html', context)


# =========================================================
# =   ЭТАПЫ (CRUD)                                        =
# =========================================================

@login_required
@user_passes_test(is_manager)
def stage_create(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    
    if request.method == 'POST':
        form = StageForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                stage = form.save(commit=False)
                stage.order = order
                last_stage = order.stages.order_by('number').last()
                stage.number = (last_stage.number + 1) if last_stage else 1
                stage.save()
                form.save_m2m()
            messages.success(request, f'Этап "{stage.name}" добавлен в заказ {order.number}!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = StageForm()
    
    context = {
        'form': form,
        'order': order,
        'title': f'Добавление этапа в заказ {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_form.html', context)


@login_required
@user_passes_test(is_manager)
def stage_detail(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    context = {
        'stage': stage,
        'active_menu': 'orders',
        'title': f'Этап {stage.number}: {stage.name}',
    }
    return render(request, 'orders/stage_detail.html', context)


@login_required
@user_passes_test(is_manager)
def stage_edit(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    if request.method == 'POST':
        form = StageForm(request.POST, request.FILES, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, f'Этап "{stage.name}" обновлён!')
            return redirect('orders:order_detail', pk=order_pk)
    else:
        form = StageForm(instance=stage)
    
    context = {
        'form': form,
        'stage': stage,
        'order': stage.order,
        'title': f'Редактирование этапа {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_form.html', context)


@login_required
@user_passes_test(is_manager)
def stage_delete(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    if request.method == 'POST':
        stage.delete()
        messages.success(request, f'Этап "{stage.name}" удалён!')
        return redirect('orders:order_detail', pk=order_pk)
    
    context = {
        'stage': stage,
        'order': stage.order,
        'title': f'Удаление этапа {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_confirm_delete.html', context)


# =========================================================
# =   ЧЕРТЕЖИ (DRAWING)                                   =
# =========================================================

@login_required
@user_passes_test(is_manager)
def drawing_create(request, order_pk, stage_pk):
    stage = get_object_or_404(Stage, pk=stage_pk, order_id=order_pk)
    
    if request.method == 'POST':
        form = DrawingForm(request.POST, request.FILES)
        if form.is_valid():
            drawing = form.save(commit=False)
            drawing.stage = stage
            drawing.uploaded_by = request.user
            last_drawing = stage.drawings.order_by('-version').first()
            drawing.version = (last_drawing.version + 1) if last_drawing else 1
            drawing.save()
            messages.success(request, f'Чертеж "{drawing.name}" загружен!')
            return redirect('orders:stage_detail', order_pk=order_pk, pk=stage_pk)
    else:
        form = DrawingForm()
    
    context = {
        'form': form,
        'stage': stage,
        'order': stage.order,
        'title': f'Загрузка чертежа к этапу {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/drawing_form.html', context)


@login_required
@user_passes_test(is_manager)
def drawing_delete(request, order_pk, stage_pk, pk):
    drawing = get_object_or_404(Drawing, pk=pk, stage_id=stage_pk, stage__order_id=order_pk)
    if request.method == 'POST':
        drawing.delete()
        messages.success(request, f'Чертеж "{drawing.name}" удалён!')
        return redirect('orders:stage_detail', order_pk=order_pk, pk=stage_pk)
    
    context = {
        'drawing': drawing,
        'stage': drawing.stage,
        'order': drawing.stage.order,
        'title': f'Удаление чертежа {drawing.name}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/drawing_confirm_delete.html', context)


# =========================================================
# =   ЛИЧНЫЙ КАБИНЕТ СОТРУДНИКА                           =
# =========================================================

@login_required
def employee_tasks(request):
    """Личный кабинет сотрудника: список его задач"""
    # Проверяем, есть ли у пользователя анкета сотрудника
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'orders/employee_tasks.html', {
            'error': 'Анкета сотрудника не заполнена. Обратитесь к администратору'
        })
        
    # Получаем уровень доступа из должности (через абстракцию).
    access_level = employee.get_access_level()
    
    # Если у сотрудника уровень доступа 'employee' или 'master' - показываем задачи.
    if access_level in ['employee', 'master']:
        # Базовый запрос: задачи, назначенные на этого сотрудника
        stages = Stage.objects.filter(
            assigned_employee=employee
        ).select_related('order', 'department', 'required_skill').order_by('planned_start_date')
        
        # Если мастер - показываем задачи всего участка
        if access_level == 'master' and employee.department:
            stages = Stage.objects.filter(
                department=employee.department
            ).exclude(
                assigned_employee=employee
            ).select_related('order', 'department', 'required_skill').order_by('planned_start_date')
            
    # Если у сотрудника другой уровень доступа - редирект (или ошибка)
    else:
        return redirect('orders:order_list')
    
    context = {
        'stages': stages,
        'employee': employee,
        'access_level': access_level,
        'active_menu': 'employee_tasks',
        'title': 'Мои задачи'
    }
    return render(request, 'orders/employee_tasks.html', context)


# ==========================================================
# = ДЕЙСТВИЯ СОТРУДНИКА (START, COMPLETE, DEFECT, PROBLEM) =
# ==========================================================

@login_required
def stage_start(request, pk):
    """Сотрудник начинает работу над этапом"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if stage.status == Stage.Status.ASSIGNED:
        stage.status = Stage.Status.IN_PROGRESS
        stage.actual_start_date = timezone.now().date()
        stage.save()
        messages.success(request, f'Этап "{stage.name}" начат!')
    else:
        messages.error(request, 'Этот этап уже в работе или завершён')

    return redirect('orders:employee_tasks')


@login_required
def stage_complete(request, pk):
    """Сотрудник завершает этап"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if stage.status == Stage.Status.IN_PROGRESS:
        stage.status = Stage.Status.COMPLETED
        stage.actual_finish_date = timezone.now().date()
        stage.save()
        messages.success(request, f'Этап "{stage.name}" завершён!')
    else:
        messages.error(request, 'Этот этап нельзя завершить')

    return redirect('orders:employee_tasks')


@login_required
def stage_defect(request, pk):
    """Сотрудник сообщает о браке"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if request.method == 'POST':
        description = request.POST.get('defect_description')
        material = request.POST.get('defect_material', '')

        if not description:
            messages.error(request, 'Опишите брак')
            return redirect('orders:employee_tasks')

        # Меняем статус и сохраняем комментарий
        stage.status = Stage.Status.DEFECT
        stage.comment = f"Брак: {description}. Материал: {material}"
        stage.save()

        messages.warning(request, f'Брак зафиксирован на этапе "{stage.name}"')

    return redirect('orders:employee_tasks')


@login_required
def stage_problem(request, pk):
    """Сотрудник сообщает о проблеме"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if request.method == 'POST':
        description = request.POST.get('problem_description')

        if not description:
            messages.error(request, 'Опишите проблему')
            return redirect('orders:employee_tasks')

        stage.status = Stage.Status.PROBLEM
        stage.comment = f"Проблема: {description}"
        stage.save()

        messages.warning(request, f'Проблема зафиксирована на этапе "{stage.name}"')

    return redirect('orders:employee_tasks')
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # --- БАЗОВЫЙ ЗАПРОС ---
    # Для директора или админа все заявки, если менеджер - только свои
    if request.user.role in ['director', 'admin']:
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(responsible_manager=request.user)
        
    # Применяем фильтры
    if status_filter:
        orders = orders.filter(status=status_filter)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
        
    # --- СТАТИСТИКА ---
    total_orders = orders.count()
    in_progress = orders.filter(status=Order.Status.IN_PROGRESS).count()
    completed = orders.filter(status=Order.Status.COMPLETED).count()
    cancelled = orders.filter(status=Order.Status.CANCELLED).count()
    draft = orders.filter(status=Order.Status.DRAFT).count()
    
    # Просроченные заказы
    overdue = orders.filter(
        status=Order.Status.IN_PROGRESS,
        planned_completion_date__lt=timezone.now().date()
    ).count()
    
    # Процент выполнения
    completion_rate = int((completed / total_orders * 100)) if total_orders > 0 else 0
    
    # --- АКТИВНЫЕ ЗАКАЗЫ (для таблицы) ---
    active_orders = orders.filter(
        status__in=[Order.Status.IN_PROGRESS, Order.Status.DRAFT]
    ).select_related('responsible_manager').prefetch_related('stages')[:20]
    
    # Добавляем прогресс для каждого заказа
    for order in active_orders:
        total_stages = order.stages.count()
        completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
        order.progress = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0
        order.completed_count = completed_stages
        order.is_overdue = (
            order.status == Order.Status.IN_PROGRESS and
            order.planned_completion_date and
            order.planned_completion_date < timezone.now().date()
        )
    
    # --- ДАННЫЕ ДЛЯ ГРАФИКОВ (ПРОДВИНУТЫЙ РЕЖИМ) ---
    
    # 1. Статусы для круговой диаграммы
    status_data = []
    status_colors = {
        'draft': '#6c757d',
        'in_progress': '#0d6efd',
        'completed': '#198754',
        'cancelled': '#dc3545',
    }
    for status_code, status_label in Order.Status.choices:
        count = orders.filter(status=status_code).count()
        if count > 0:
            status_data.append({
                'label': status_label,
                'value': count,
                'color': status_colors.get(status_code, '#6c757d')
            })
    
    # 2. Динамика заказов по дням (последние 30 дней)
    today = timezone.now().date()
    days_ago = 30
    
    daily_stats = orders.filter(
        created_at__date__gte=today - timedelta(days=days_ago)
    ).extra(
        {'day': 'date(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Заполняем массив для всех дней
    daily_labels = []
    daily_values = []
    for i in range(days_ago):
        day = today - timedelta(days=days_ago - i - 1)
        daily_labels.append(day.strftime('%d.%m'))
        daily_values.append(0)
    
    for stat in daily_stats:
        day_str = stat['day'].strftime('%d.%m')
        if day_str in daily_labels:
            idx = daily_labels.index(day_str)
            daily_values[idx] = stat['count']
    
    # 3. Загрузка сотрудников (если модуль employees активен)
    employee_load = []
    if apps.is_installed('employees'):
        from employees.models import Employee
        employees = Employee.objects.filter(status='active').select_related('user')[:10]
        for emp in employees:
            active = Stage.objects.filter(
                assigned_employee=emp,
                status__in=[Stage.Status.ASSIGNED, Stage.Status.IN_PROGRESS]
            ).count()
            in_work = Stage.objects.filter(
                assigned_employee=emp,
                status=Stage.Status.IN_PROGRESS
            ).count()
            employee_load.append({
                'name': emp.full_name,
                'active': active,
                'in_work': in_work,
                'load': active * 2  # Условная загрузка (1 задача = 2 часа)
            })
    
    # 4. Загрузка участков (для директора)
    department_load = []
    if apps.is_installed('employees') and request.user.role in ['director', 'admin']:
        from employees.models import Department
        departments = Department.objects.all()
        for dept in departments:
            active_stages = Stage.objects.filter(
                department=dept,
                status__in=[Stage.Status.IN_PROGRESS, Stage.Status.ASSIGNED]
            ).count()
            total_stages = Stage.objects.filter(department=dept).count()
            load_percent = int((active_stages / total_stages * 100)) if total_stages > 0 else 0
            department_load.append({
                'name': dept.name,
                'active': active_stages,
                'total': total_stages,
                'load': load_percent
            })
    
    # 5. Топ-менеджеры (для директора)
    top_managers = []
    if request.user.role in ['director', 'admin']:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        top_managers = User.objects.filter(
            managed_orders__isnull=False
        ).annotate(
            order_count=Count('managed_orders')
        ).order_by('-order_count')[:5]
    
    context = {
        'mode': mode,
        # Статистика
        'total_orders': total_orders,
        'in_progress': in_progress,
        'completed': completed,
        'cancelled': cancelled,
        'draft': draft,
        'overdue': overdue,
        'completion_rate': completion_rate,
        # Активные заказы
        'active_orders': active_orders,
        # Данные для графиков
        'status_data': status_data,
        'daily_labels': daily_labels,
        'daily_values': daily_values,
        'employee_load': employee_load,
        'department_load': department_load,
        'top_managers': top_managers,
        # Навигация
        'active_menu': 'dashboard',
        'title': 'Дашборд',
    }
    
    return render(request, 'orders/manager_dashboard.html', context)
    
       

# =========================================================
# =                   ЗАКАЗЫ (CRUD)                       =
# =========================================================

@login_required
@user_passes_test(is_manager)
def order_list(request):
    """Список заказов с фильтрацией"""
    
    # Базовый запрос с учетом прав
    if request.user.is_superuser or request.user.role in ['admin', 'director']:
        # Администраторы видят все заказы, включая удаленные
        orders = Order.objects.select_related(
            'customer', 'responsible_manager'
        ).prefetch_related('stages').all()
        
        # Но по умолчанию скрываем удаленные (можно показать через параметр)
        show_deleted = request.GET.get('show_deleted', 'false') == 'true'
        if not show_deleted:
            orders = orders.filter(is_deleted=False)
            
    else:
        # Менеджер - только свои, не удаленные
        orders = Order.objects.select_related(
            'customer', 'responsible_manager'
        ).prefetch_related('stages').filter(
            responsible_manager=request.user,
            is_deleted=False
        )
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Фильтр по приоритету
    priority = request.GET.get('priority')
    if priority:
        orders = orders.filter(priority=priority)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(number__icontains=search) |
            Q(name__icontains=search) |
            Q(customer__name__icontains=search)
        )
    
    # Добавляем прогресс через сервис
    orders = OrderProgressService.get_orders_with_progress(orders)
    
    context = {
        'orders': orders,
        'statuses': Order.Status.choices,
        'active_menu': 'orders',
        'title': 'Заказы',
        'show_deleted': request.GET.get('show_deleted', 'false') == 'true',
        'is_admin': request.user.is_superuser or request.user.role in ['admin', 'director'],
    }
    return render(request, 'orders/order_list.html', context)


@login_required
@user_passes_test(is_manager)
def order_detail(request, pk):
    """Детальная страница заказа"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем доступ к удаленному заказу
    if order.is_deleted:
        if not (request.user.is_superuser or request.user.role in ['admin', 'director']):
            messages.error(request, 'Заказ был удален и недоступен для просмотра.')
            return redirect('orders:order_list')
    
    # Используем сервис для расчёта
    progress = OrderProgressService.get_progress_percent(order)
    completed_count = OrderProgressService.get_completed_stages_count(order)
    
    # Подготовка данных для Гант-диаграмм
    gantt_data = []
    for stage in order.stages.all().order_by('number'):
        # Определяем цвет статуса для Гант
        status_colors = {
            'pending': '#6c757d',       # серый
            'assigned': '#0d6efd',      # синий
            'in_progress': '#0dca0d',   # голубой
            'completed': '#198754',     # зеленый
            'defect': '#dc3545',        # красный
            'problem': '#ffc107',       # желтый
            'on_hold': '#fd7e14',       # оранжевый
        }
        
        gantt_data.append({
            'id': str(stage.id),
            'name': f'Этап {stage.number}: {stage.name}',
            'start': stage.planned_start_date.strftime('%Y-%m-%d') if stage.planned_start_date else None,
            'end': stage.planned_finish_date.strftime('%Y-%m-%d') if stage.planned_finish_date else None,
            'progress': 100 if stage.status == 'completed' else 0,
            'custom_class': stage.status,
            'color': status_colors.get(stage.status, '#6c757d'),
        })
    
    context = {
        'order': order,
        'progress': progress,
        'completed_count': completed_count,
        'gantt_data': json.dumps(gantt_data),    # Передаем в JSON
        'active_menu': 'orders',
        'title': f'{order.number} — {order.name}',
        'is_admin': request.user.is_superuser or request.user.role in ['admin', 'director'],
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@user_passes_test(is_manager)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        
        # ✅ ОТЛАДКА: выводим ошибки формы
        if not form.is_valid():
            print("❌ ФОРМА НЕ ВАЛИДНА!")
            print(form.errors)
            print(form.cleaned_data)
        else:
            print("✅ ФОРМА ВАЛИДНА")
            print(form.cleaned_data)
        
        if form.is_valid():
            order = form.save(commit=False)
            order.save()
            form.save_m2m()
            messages.success(request, f'Заказ {order.number} успешно создан!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'title': 'Создание заказа',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_form.html', context)


@login_required
@user_passes_test(is_manager)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Заказ {order.number} успешно обновлён!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'Редактирование заказа {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_form.html', context)

@login_required
@user_passes_test(is_manager)
@require_POST
def order_upload_files(request, pk):
    """Загрузка файлов к заказу (AJAX)"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем права
    if order.is_deleted:
        if not (request.user.is_superuser or request.user.role in ['admin', 'director']):
            return JsonResponse({'success': False, 'error': 'Заказ удален'})
    
    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'success': False, 'error': 'Файлы не выбраны'})
    
    uploaded_files = []
    for f in files:
        file_obj = OrderFile.objects.create(
            name=f.name,
            file=f,
            file_type=OrderFile.FileType.OTHER,
            uploaded_by=request.user,
        )
        order.files.add(file_obj)
        uploaded_files.append({
            'name': file_obj.name,
            'url': file_obj.file.url,
            'type': file_obj.get_file_type_display(),
            'version': 1
        })
    
    return JsonResponse({
        'success': True,
        'files': uploaded_files
    })

@login_required
@user_passes_test(is_manager)
def order_delete(request, pk):
    """Удаление заказа (мягкое удаление)"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем права: только директор или админ могут удалять
    if not (request.user.is_superuser or request.user.role in ['admin', 'director']):
        messages.error(request, 'У вас нет прав на удаление заказов. Обратитесь к администратору.')
        return redirect('orders:order_detail', pk=order.pk)
    
    # Проверяем, не удален ли уже заказ
    if order.is_deleted:
        messages.warning(request, f'Заказ {order.number} уже удален.')
        return redirect('orders:order_list')
    
    if request.method == 'POST':
        # Мягкое удаление
        order.soft_delete(request.user)
        messages.success(request, f'Заказ {order.number} помечен на удаление. Он будет скрыт из общего списка.')
        return redirect('orders:order_list')
    
    context = {
        'order': order,
        'title': f'Удаление заказа {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/order_confirm_delete.html', context)

@login_required
@user_passes_test(is_manager)
def order_restore(request, pk):
    """Восстановление удаленного заказа"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем права: только директор или админ могут восстанавливать
    if not (request.user.is_superuser or request.user.role in ['admin', 'director']):
        messages.error(request, 'У вас нет прав на восстановление заказов.')
        return redirect('orders:order_detail', pk=order.pk)
    
    if not order.is_deleted:
        messages.warning(request, f'Заказ {order.number} не был удален.')
        return redirect('orders:order_detail', pk=order.pk)
    
    if request.method == 'POST':
        order.restore()
        messages.success(request, f'Заказ {order.number} успешно восстановлен!')
        return redirect('orders:order_detail', pk=order.pk)
    
    return redirect('orders:order_detail', pk=order.pk)

# =========================================================
# =   ЭТАПЫ (CRUD)                                        =
# =========================================================

@login_required
@user_passes_test(is_manager)
def stage_create(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    
    if request.method == 'POST':
        form = StageForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                stage = form.save(commit=False)
                stage.order = order
                last_stage = order.stages.order_by('number').last()
                stage.number = (last_stage.number + 1) if last_stage else 1
                stage.save()
                form.save_m2m()
            messages.success(request, f'Этап "{stage.name}" добавлен в заказ {order.number}!')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = StageForm()
    
    context = {
        'form': form,
        'order': order,
        'title': f'Добавление этапа в заказ {order.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_form.html', context)


@login_required
@user_passes_test(is_manager)
def stage_detail(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    context = {
        'stage': stage,
        'active_menu': 'orders',
        'title': f'Этап {stage.number}: {stage.name}',
    }
    return render(request, 'orders/stage_detail.html', context)


@login_required
@user_passes_test(is_manager)
def stage_edit(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    if request.method == 'POST':
        form = StageForm(request.POST, request.FILES, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, f'Этап "{stage.name}" обновлён!')
            return redirect('orders:order_detail', pk=order_pk)
    else:
        form = StageForm(instance=stage)
    
    context = {
        'form': form,
        'stage': stage,
        'order': stage.order,
        'title': f'Редактирование этапа {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_form.html', context)


@login_required
@user_passes_test(is_manager)
def stage_delete(request, order_pk, pk):
    stage = get_object_or_404(Stage, pk=pk, order_id=order_pk)
    if request.method == 'POST':
        stage.delete()
        messages.success(request, f'Этап "{stage.name}" удалён!')
        return redirect('orders:order_detail', pk=order_pk)
    
    context = {
        'stage': stage,
        'order': stage.order,
        'title': f'Удаление этапа {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/stage_confirm_delete.html', context)


# =========================================================
# =   ЧЕРТЕЖИ (DRAWING)                                   =
# =========================================================

@login_required
@user_passes_test(is_manager)
def drawing_create(request, order_pk, stage_pk):
    stage = get_object_or_404(Stage, pk=stage_pk, order_id=order_pk)
    
    if request.method == 'POST':
        form = DrawingForm(request.POST, request.FILES)
        if form.is_valid():
            drawing = form.save(commit=False)
            drawing.stage = stage
            drawing.uploaded_by = request.user
            last_drawing = stage.drawings.order_by('-version').first()
            drawing.version = (last_drawing.version + 1) if last_drawing else 1
            drawing.save()
            messages.success(request, f'Чертеж "{drawing.name}" загружен!')
            return redirect('orders:stage_detail', order_pk=order_pk, pk=stage_pk)
    else:
        form = DrawingForm()
    
    context = {
        'form': form,
        'stage': stage,
        'order': stage.order,
        'title': f'Загрузка чертежа к этапу {stage.number}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/drawing_form.html', context)


@login_required
@user_passes_test(is_manager)
def drawing_delete(request, order_pk, stage_pk, pk):
    drawing = get_object_or_404(Drawing, pk=pk, stage_id=stage_pk, stage__order_id=order_pk)
    if request.method == 'POST':
        drawing.delete()
        messages.success(request, f'Чертеж "{drawing.name}" удалён!')
        return redirect('orders:stage_detail', order_pk=order_pk, pk=stage_pk)
    
    context = {
        'drawing': drawing,
        'stage': drawing.stage,
        'order': drawing.stage.order,
        'title': f'Удаление чертежа {drawing.name}',
        'active_menu': 'orders',
    }
    return render(request, 'orders/drawing_confirm_delete.html', context)


# =========================================================
# =   ЛИЧНЫЙ КАБИНЕТ СОТРУДНИКА                           =
# =========================================================

@login_required
def employee_tasks(request):
    """Личный кабинет сотруднкиа: список его задач"""
    # Проверяем, есть ли у пользователя анкета сотрудника
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'orders/employee_tasks.html', {
            'error': 'Анкета сотрудника не заполнена. Обратитесь к администратору'
        })
        
    # Получаем уровень доступа из должности (через абстракцию).
    access_level = employee.get_access_level()
    
    # Если у сотрудника уровень доступа 'employee' или 'master' - показываем задачи.
    if access_level in ['employee', 'master']:
        # Базовый запрос: задачи, назначенные на этого сотрудника
        stages = Stage.objects.filter(
            assigned_employee=employee
        ).select_related('order', 'department', 'required_skill').order_by('planned_start_date')
        
        # Если мастер - показываем задачи всего участка
        if access_level == 'master' and employee.department:
            stages = Stage.objects.filter(
                department=employee.department
            ).exclude(
                assigned_employee=employee
            ).select_related('order', 'department', 'required_skill').order_by('planned_start_date')
            
    # Если у сотруднкка другой уровень доступа - редирект (или ошибка)
    else:
        return redirect('orders:order_list')
    
    context = {
        'stages': stages,
        'employee': employee,
        'access_level': access_level,
        'active_menu': 'employee_tasks',
        'title': 'Мои задачи'
    }
    return render(request, 'orders/employee_tasks.html', context)


# ==========================================================
# = ДЕЙСТВИЯ СОТРУДНИКА (START, COMPLETE, DEFECT, PROBLEM) =
# ==========================================================

@login_required
def stage_start(request, pk):
    """Сотрудник начинает работу над этапом"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if stage.status == Stage.Status.ASSIGNED:
        stage.status = Stage.Status.IN_PROGRESS
        stage.actual_start_date = timezone.now().date()
        stage.save()
        messages.success(request, f'Этап "{stage.name}" начат!')
    else:
        messages.error(request, 'Этот этап уже в работе или завершён')

    return redirect('orders:employee_tasks')


@login_required
def stage_complete(request, pk):
    """Сотрудник завершает этап"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if stage.status == Stage.Status.IN_PROGRESS:
        stage.status = Stage.Status.COMPLETED
        stage.actual_finish_date = timezone.now().date()
        stage.save()
        messages.success(request, f'Этап "{stage.name}" завершён!')
    else:
        messages.error(request, 'Этот этап нельзя завершить')

    return redirect('orders:employee_tasks')


@login_required
def stage_defect(request, pk):
    """Сотрудник сообщает о браке"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if request.method == 'POST':
        description = request.POST.get('defect_description')
        material = request.POST.get('defect_material', '')

        if not description:
            messages.error(request, 'Опишите брак')
            return redirect('orders:employee_tasks')

        # Меняем статус и сохраняем комментарий
        stage.status = Stage.Status.DEFECT
        stage.comment = f"Брак: {description}. Материал: {material}"
        stage.save()

        messages.warning(request, f'Брак зафиксирован на этапе "{stage.name}"')

    return redirect('orders:employee_tasks')


@login_required
def stage_problem(request, pk):
    """Сотрудник сообщает о проблеме"""
    stage = get_object_or_404(Stage, pk=pk, assigned_employee=request.user.employee)

    if request.method == 'POST':
        description = request.POST.get('problem_description')

        if not description:
            messages.error(request, 'Опишите проблему')
            return redirect('orders:employee_tasks')

        stage.status = Stage.Status.PROBLEM
        stage.comment = f"Проблема: {description}"
        stage.save()

        messages.warning(request, f'Проблема зафиксирована на этапе "{stage.name}"')

    return redirect('orders:employee_tasks')