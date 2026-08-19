# employees/iews.py | A.Grachev
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import (
    Employee, 
    Department, 
    Skill, 
    Position, 
    EmployeeSkill,
)
from .forms import (
    EmployeeForm, 
    DepartmentForm,
    SkillForm,
    PositionForm,
)


# =========================================================
# =   ПРОВЕРКА ПРАВ                                       =
# =========================================================
def is_manager(user):
    """Проверка: пользователь может управлять справочниками"""
    if user.is_superuser:
        return True
    return user.is_authenticated and user.role in ['admin', 'director', 'manager']


# =========================================================
# =   СОТРУДНИКИ                                          =
# =========================================================
@login_required
@user_passes_test(is_manager)
def employee_list(request):
    """Список сотрудников с фильтром"""
    employees = Employee.objects.select_related('department', 'position').exclude(
        user__is_superuser=True
    ).all()
    departments = Department.objects.all()
    
    # Фильтр по участку (через GET-параметр)
    department_id = request.GET.get('department')
    if department_id:
        employees = employees.filter(department_id=department_id)
        
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        employees = employees.filter(status=status)
        
    # Поиск
    search = request.GET.get('search')
    if search:
        employees = employees.filter(
            Q(last_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(patronymic__icontains=search) |
            Q(personal_number__icontains=search)
        )
        
    context = {
        'employees': employees,
        'departments': departments,
        'active_menu': 'employees',
        'title': 'Сотрудники',
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
@user_passes_test(is_manager)
def employee_detail(request, pk):
    """Детальная страница сотрудника"""
    employee = get_object_or_404(Employee, pk=pk)
    skills = Skill.objects.all().order_by('name')
    
    # Получаем историю сотрудника
    history_all = list(employee.history.all().order_by('history_date'))
    
    # Добавляем историю навыков
    skill_history = EmployeeSkill.history.filter(employee_id=pk).order_by('history_date')
    
    # Объединяем историю сотрудника и навыков
    combined_history = list(history_all) + list(skill_history)
    combined_history.sort(key=lambda x: x.history_date)
    
    # Добавляем атрибут history_delta_changes к каждой записи
    for i, current in enumerate(combined_history):
        if i == 0:
            current.history_delta_changes = None
        else:
            previous = combined_history[i - 1]
            # Проверяем, что это один и тот же тип объекта
            if type(current) == type(previous):
                try:
                    delta = current.diff_against(previous, foreign_keys_are_objs=True)
                    if delta:
                        from simple_history.template_utils import HistoricalRecordContextHelper
                        # Определяем модель для helper
                        model = Employee if isinstance(current, Employee.history.model) else EmployeeSkill
                        helper = HistoricalRecordContextHelper(model, current)
                        current.history_delta_changes = helper.context_for_delta_changes(delta)
                    else:
                        current.history_delta_changes = None
                except:
                    current.history_delta_changes = None
            else:
                # Разные типы записей - показываем как создание/изменение
                current.history_delta_changes = None
    
    # Берем только последние 5 записей
    history_last_5 = list(reversed(combined_history))[:5]
    
    context = {
        'employee': employee,
        'skills': skills,
        'history': history_last_5,
        'history_count': len(combined_history),
        'active_menu': 'employees',
        'title': str(employee),
    }
    return render(request, 'employees/employee_detail.html', context)


@login_required
@user_passes_test(is_manager)
def employee_history(request, pk):
    """Полная история изменений сотрудника с пагинацией"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Получаем историю сотрудника
    history_all = list(employee.history.all().order_by('history_date'))
    
    # Получаем историю навыков
    skill_history = EmployeeSkill.history.filter(employee_id=pk).order_by('history_date')
    
    # Объединяем историю
    combined_history = list(history_all) + list(skill_history)
    combined_history.sort(key=lambda x: x.history_date)
    
    # Добавляем атрибут history_delta_changes к каждой записи
    for i, current in enumerate(combined_history):
        if i == 0:
            current.history_delta_changes = None
        else:
            previous = combined_history[i - 1]
            if type(current) == type(previous):
                try:
                    delta = current.diff_against(previous, foreign_keys_are_objs=True)
                    if delta:
                        from simple_history.template_utils import HistoricalRecordContextHelper
                        model = Employee if isinstance(current, Employee.history.model) else EmployeeSkill
                        helper = HistoricalRecordContextHelper(model, current)
                        current.history_delta_changes = helper.context_for_delta_changes(delta)
                    else:
                        current.history_delta_changes = None
                except:
                    current.history_delta_changes = None
            else:
                current.history_delta_changes = None
    
    # Переворачиваем для отображения (сначала новые)
    history_with_changes = list(reversed(combined_history))
    
    # Пагинация
    paginator = Paginator(history_with_changes, 20)
    page_number = request.GET.get('page')
    history_page = paginator.get_page(page_number)
    
    context = {
        'employee': employee,
        'history_page': history_page,
        'history_count': len(history_with_changes),
        'active_menu': 'employees',
        'title': f'История изменений: {employee}',
    }
    return render(request, 'employees/employee_history.html', context)


@login_required
@user_passes_test(is_manager)
def employee_create(request):
    """Создание сотрудника"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Сотрудник {employee} успешно создан!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()

    context = {
        'form': form,
        'title': 'Добавление сотрудника',
        'active_menu': 'employees',
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
@user_passes_test(is_manager)
def employee_edit(request, pk):
    """Редактирование сотрудника"""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Сотрудник {employee} успешно обновлён!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    context = {
        'form': form,
        'employee': employee,
        'title': 'Редактирование сотрудника',
        'active_menu': 'employees',
    }
    return render(request, 'employees/employee_form.html', context)


@login_required
@user_passes_test(is_manager)
def employee_delete(request, pk):
    """Удаление сотрудника"""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Сотрудник успешно удалён!')
        return redirect('employees:employee_list')

    context = {
        'employee': employee,
        'active_menu': 'employees',
        'title': 'Удаление сотрудника',
    }
    return render(request, 'employees/employee_confirm_delete.html', context)


# =========================================================
# =   УЧАСТКИ                                             =
# =========================================================
@login_required
@user_passes_test(is_manager)
def department_list(request):
    departments = Department.objects.all()
    context = {
        'departments': departments,
        'active_menu': 'departments',
        'title': 'Участки',
    }
    return render(request, 'employees/department_list.html', context)


@login_required
@user_passes_test(is_manager)
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Участок успешно создан!')
            return redirect('employees:department_list')
    else:
        form = DepartmentForm()

    context = {
        'form': form,
        'title': 'Добавление участка',
        'active_menu': 'departments',
    }
    return render(request, 'employees/department_form.html', context)


@login_required
@user_passes_test(is_manager)
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, 'Участок успешно обновлён!')
            return redirect('employees:department_list')
    else:
        form = DepartmentForm(instance=dept)

    context = {
        'form': form,
        'department': dept,
        'title': 'Редактирование участка',
        'active_menu': 'departments',
    }
    return render(request, 'employees/department_form.html', context)


@login_required
@user_passes_test(is_manager)
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Участок успешно удалён!')
        return redirect('employees:department_list')

    context = {
        'department': dept,
        'active_menu': 'departments',
        'title': 'Удаление участка',
    }
    return render(request, 'employees/department_confirm_delete.html', context)


# =========================================================
# =   НАВЫКИ                                              =
# =========================================================
@login_required
@user_passes_test(is_manager)
def skill_list(request):
    skills = Skill.objects.all()
    context = {
        'skills': skills,
        'active_menu': 'skills',
        'title': 'Навыки',
    }
    return render(request, 'employees/skill_list.html', context)


@login_required
@user_passes_test(is_manager)
def skill_create(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Навык успешно создан!')
            return redirect('employees:skill_list')
    else:
        form = SkillForm()

    context = {
        'form': form,
        'title': 'Добавление навыка',
        'active_menu': 'skills',
    }
    return render(request, 'employees/skill_form.html', context)


@login_required
@user_passes_test(is_manager)
def skill_edit(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Навык успешно обновлён!')
            return redirect('employees:skill_list')
    else:
        form = SkillForm(instance=skill)

    context = {
        'form': form,
        'skill': skill,
        'title': 'Редактирование навыка',
        'active_menu': 'skills',
    }
    return render(request, 'employees/skill_form.html', context)


@login_required
@user_passes_test(is_manager)
def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Навык успешно удалён!')
        return redirect('employees:skill_list')

    context = {
        'skill': skill,
        'active_menu': 'skills',
        'title': 'Удаление навыка',
    }
    return render(request, 'employees/skill_confirm_delete.html', context)


# =========================================================
# =   ДОЛЖНОСТИ                                           =
# =========================================================
@login_required
@user_passes_test(is_manager)
def position_list(request):
    """Список должностей"""
    positions = Position.objects.all()
    context = {
        'positions': positions,
        'active_menu': 'positions',
        'title': 'Должности',
    }
    return render(request, 'employees/position_list.html', context)


@login_required
@user_passes_test(is_manager)
def position_create(request):
    """Создание должности"""
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Должность успешно создана!')
            return redirect('employees:position_list')
    else:
        form = PositionForm()

    context = {
        'form': form,
        'title': 'Добавление должности',
        'active_menu': 'positions',
    }
    return render(request, 'employees/position_form.html', context)


@login_required
@user_passes_test(is_manager)
def position_edit(request, pk):
    """Редактирование должности"""
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, 'Должность успешно обновлена!')
            return redirect('employees:position_list')
    else:
        form = PositionForm(instance=position)

    context = {
        'form': form,
        'position': position,
        'title': 'Редактирование должности',
        'active_menu': 'positions',
    }
    return render(request, 'employees/position_form.html', context)


@login_required
@user_passes_test(is_manager)
def position_delete(request, pk):
    """Удаление должности"""
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        position.delete()
        messages.success(request, 'Должность успешно удалена!')
        return redirect('employees:position_list')

    context = {
        'position': position,
        'active_menu': 'positions',
        'title': 'Удаление должности',
    }
    return render(request, 'employees/position_confirm_delete.html', context)


# =========================================================
# =   МАТРИЦА КВАЛИФИКАЦИЙ                                =
# =========================================================
@login_required
@user_passes_test(is_manager)
def skill_matrix(request):
    """Матрица квалификаций: сотрудник х навыки"""
    # ✅ ИСПРАВЛЕНО: исключаем суперпользователей
    employees = Employee.objects.select_related('department').exclude(
        user__is_superuser=True
    ).all()
    
    skills = Skill.objects.all().order_by('name')
    departments = Department.objects.all()
    
    # Собираем данные для матрицы
    matrix = []
    for employee in employees:
        # Словарь: {skill_id: level}
        skill_levels = {es.skill_id: es.level for es in employee.employeeskill_set.all()}
        matrix.append({
            'employee': employee,
            'levels': skill_levels,
        })
        
    context = {
        'matrix': matrix,
        'skills': skills,
        'departments': departments,
        'active_menu': 'skill_matrix',
        'title': 'Матрица квалификаций'
    }
    
    return render(request, 'employees/skill_matrix.html', context)


@login_required
@user_passes_test(is_manager)
@require_POST
def employee_add_skill(request, pk):
    """Добавление навыка сотруднику (AJAX)"""
    employee = get_object_or_404(Employee, pk=pk)
    
    try:
        import json
        data = json.loads(request.body)
        skill_id = data.get('skill_id')
        level = data.get('level', 1)
        
        if not skill_id:
            return JsonResponse({'success': False, 'error': 'Навык не указан'})
        
        skill = get_object_or_404(Skill, pk=skill_id)
        
        # Проверяем, есть ли уже такой навык
        employee_skill, created = EmployeeSkill.objects.get_or_create(
            employee=employee,
            skill=skill,
            defaults={'level': level}
        )
        
        if not created:
            # Обновляем уровень
            employee_skill.level = level
            employee_skill.save()
        
        return JsonResponse({
            'success': True,
            'skill_id': skill.pk,
            'skill_name': skill.name,
            'level': level
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_manager)
@require_POST
def employee_remove_skill(request, pk):
    """Удаление навыка у сотрудника (AJAX)"""
    employee = get_object_or_404(Employee, pk=pk)
    
    try:
        import json
        data = json.loads(request.body)
        skill_id = data.get('skill_id')
        
        if not skill_id:
            return JsonResponse({'success': False, 'error': 'Навык не указан'})
        
        employee.employeeskill_set.filter(skill_id=skill_id).delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
# =========================================================
# =   ГЛАВНАЯ СТРАНИЦА (РЕДИРЕКТ ПО РОЛЯМ)                =
# =========================================================
@login_required
def home_redirect(request):
    """Перенаправляет пользователя на его рабочую страницу в зависимости от роли"""
    user = request.user
    
    # Если пользователь — сотрудник (есть анкета)
    if hasattr(user, 'employee') and user.employee:
        employee = user.employee
        access_level = employee.get_access_level()
        
        # Сотрудник → Мои задачи
        if access_level == 'employee':
            return redirect('orders:employee_tasks')
        
        # Мастер → Задачи участка (пока что тоже в Мои задачи, но позже сделаем отдельно)
        elif access_level == 'master':
            # TODO: сделать отдельную страницу для мастера
            return redirect('orders:employee_tasks')
        
        # Директор → Дашборд (пока нет, редирект на список заказов)
        elif access_level == 'director' or access_level == 'admin':
            # TODO: сделать дашборд для директора
            return redirect('orders:order_list')
        
        # Менеджер → Список заказов
        elif access_level == 'manager':
            return redirect('orders:order_list')
    
    # Если у пользователя нет роли — редирект на список заказов (как менеджер)
    return redirect('orders:order_list')
