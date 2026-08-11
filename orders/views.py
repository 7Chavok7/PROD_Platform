from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.db import transaction
from .models import Order, Stage, Drawing, OrderFile
from .forms import OrderForm, StageForm, DrawingForm, OrderFileForm
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
    
    # Добавляем прогресс для каждого заказа
    for order in orders:
        total_stages = order.stages.count()
        completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
        order.progress = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0
        order.completed_count = completed_stages
    
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
    order = get_object_or_404(Order.objects.prefetch_related('stages', 'files'), pk=pk)
    
    total_stages = order.stages.count()
    completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
    progress = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0
    
    context = {
        'order': order,
        'progress': progress,
        'active_menu': 'orders',
        'title': f'{order.number} — {order.name}',
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@user_passes_test(is_manager)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.responsible_manager = request.user
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