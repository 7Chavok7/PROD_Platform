# orders/views.py | A.Grachev
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
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


def is_manager(user):
    if user.is_superuser:
        return True
    return user.is_authenticated and user.role in ['admin', 'director', 'manager', 'employee']


@login_required
def home_redirect(request):
    """
    Перенаправляет пользователя на его рабочую страницу в зависимости от роли.
    Это точка входа после логина.
    """
    user = request.user
    
    # Суперпользователь ► Дашборд менеджера (в перспективе свой дашборд)
    if user.is_superuser:
        return redirect('orders:manager_dashboard')
    
    # Проверяем активность модуля "employees"
    if apps.is_installed('employees'):
        from employees.models import Employee
        
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            messages.error(
                request,
                'Ваша учетная запись не привязана к сотруднику. Обратитесь к Администратору.'
            )
            return redirect('logout')
        
        # Определяем уровень доступа из должности
        access_level = employee.get_access_level()
        
        if access_level in ['manager', 'director', 'admin']:
            return redirect('orders:manager_dashboard')
        if access_level in ['employee', 'master']:
            return redirect('orders:employee_tasks')
    
    # Если модуль "employees" не активен ► просто список заказов
    return redirect('orders:order_list')
    

# =========================================================
# =   ЗАКАЗЫ (CRUD)                                       =
# =========================================================

@login_required
@user_passes_test(is_manager)
def order_list(request):
    """Список заказов с фильтрацией"""
    
    # Используем select_related только для полей, которые точно есть
    # responsible_manager всегда есть, customer — условно
    orders = Order.objects.select_related('responsible_manager').prefetch_related('stages').all()
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Фильтр по приоритету
    priority = request.GET.get('priority')
    if priority:
        orders = orders.filter(priority=priority)
    
    # Поиск — адаптивный, с проверкой наличия поля
    search = request.GET.get('search')
    if search:
        # Базовый поиск по номеру и названию
        search_filter = Q(number__icontains=search) | Q(name__icontains=search)
        
        # Если модуль customers активен — добавляем поиск по имени заказчика
        if apps.is_installed('customers'):
            search_filter |= Q(customer__name__icontains=search)
        
        # Всегда ищем по текстовому полю customer_name
        search_filter |= Q(customer_name__icontains=search)
        
        orders = orders.filter(search_filter)
    
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
    # Используем select_related только для полей, которые точно есть
    order = get_object_or_404(
        Order.objects.select_related('responsible_manager').prefetch_related('stages', 'files'),
        pk=pk
    )
    
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
        
        # ОТЛАДКА: выводим ошибки формы
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
    
    # Проверяем активность модуля employees
    if not apps.is_installed('employees'):
        return render(request, 'orders/employee_tasks.html', {
            'error': 'Модуль "Сотрудники" не активен. Обратитесь к администратору.'
        })
    
    from employees.models import Employee
    
    # Проверяем, есть ли у пользователя анкета сотрудника
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return render(request, 'orders/employee_tasks.html', {
            'error': 'Анкета сотрудника не заполнена. Обратитесь к администратору.'
        })
        
    # Получаем уровень доступа из должности (через абстракцию)
    access_level = employee.get_access_level()
    
    # Если у сотрудника уровень доступа 'employee' или 'master' - показываем задачи
    if access_level in ['employee', 'master']:
        # Базовый запрос: задачи, назначенные на этого сотрудника
        stages = Stage.objects.filter(
            assigned_employee=employee
        ).select_related('order').order_by('planned_start_date')
        
        # Если мастер - показываем задачи всего участка
        if access_level == 'master' and employee.department:
            stages = Stage.objects.filter(
                department=employee.department
            ).exclude(
                assigned_employee=employee
            ).select_related('order').order_by('planned_start_date')
            
    # Если у сотрудника другой уровень доступа - редирект
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


# =========================================================
# = ДЕЙСТВИЯ СОТРУДНИКА (START, COMPLETE, DEFECT, PROBLEM) =
# =========================================================

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


# =========================================================
# =   ДАШБОРД МЕНЕДЖЕРА                                   =
# =========================================================

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    """Дашборд менеджера с переключателем режимов"""
    
    # Если пользователь — сотрудник, перенаправляем его на его задачи
    if apps.is_installed('employees'):
        from employees.models import Employee
        try:
            employee = request.user.employee
            access_level = employee.get_access_level()
            if access_level == 'employee':
                return redirect('orders:employee_tasks')
        except Employee.DoesNotExist:
            pass
    
    # Получаем параметр режима из GET-запроса
    mode = request.GET.get('mode', 'minimal')
    
    # === БАЗОВАЯ СТАТИСТИКА ===
    if request.user.role in ['director', 'admin']:
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(responsible_manager=request.user)
        
    total_orders = orders.count()
    in_progress = orders.filter(status=Order.Status.IN_PROGRESS).count()
    completed = orders.filter(status=Order.Status.COMPLETED).count()
    overdue = orders.filter(
        status=Order.Status.IN_PROGRESS,
        planned_completion_date__lt=timezone.now().date()
    ).count()
    cancelled = orders.filter(status=Order.Status.CANCELLED).count()
    
    # === АКТИВНЫЕ ЗАКАЗЫ ===
    active_orders = orders.filter(
        status__in=[Order.Status.IN_PROGRESS, Order.Status.DRAFT]
    ).select_related('responsible_manager').prefetch_related('stages')[:20]
    
    for order in active_orders:
        total_stages = order.stages.count()
        completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
        order.progress = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0
        order.completed_count = completed_stages
        
    # === ДАННЫЕ ДЛЯ ГРАФИКОВ ===
    status_stage = orders.values('status').annotate(count=Count('status'))
    status_labels = {
        'draft': 'Черновик',
        'in_progress': 'В работе',
        'completed': 'Выполнен',
        'cancelled': 'Отменен'
    }
    status_data = []
    for item in status_stage:
        status_data.append({
            'label': status_labels.get(item['status'], item['status']),
            'value': item['count']
        })
        
    # Динамика заказов по дням
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    daily_stats = orders.filter(
        created_at__date__gte=week_ago
    ).extra(
        {'day': 'date(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    daily_labels = []
    daily_values = []
    for i in range(7):
        day = week_ago + timedelta(days=i+1)
        daily_labels.append(day.strftime('%d.%m'))
        daily_values.append(0)
    
    for stat in daily_stats:
        day_str = stat['day'].strftime('%d.%m')
        if day_str in daily_labels:
            idx = daily_labels.index(day_str)
            daily_values[idx] = stat['count']
            
    # === ЗАГРУЗКА СОТРУДНИКОВ ===
    employee_load = []
    if apps.is_installed('employees'):
        from employees.models import Employee
        employees = Employee.objects.filter(status='active').select_related('user')[:10]
        for emp in employees:
            load = Stage.objects.filter(
                assigned_employee=emp,
                status=Stage.Status.IN_PROGRESS
            ).count()
            employee_load.append({
                'name': emp.full_name,
                'load': load
            })
            
    context = {
        'mode': mode,
        'total_orders': total_orders,
        'in_progress': in_progress,
        'completed': completed,
        'overdue': overdue,
        'cancelled': cancelled,
        'active_orders': active_orders,
        'daily_labels': daily_labels,
        'daily_values': daily_values,
        'employee_load': employee_load,
        'active_menu': 'dashboard',
        'title': 'Дашборд',
    }
    
    return render(request, 'orders/manager_dashboard.html', context)