from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone
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
# =   ЗАКАЗЫ (CRUD)                                       =
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