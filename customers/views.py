# customers/views.py | A.Grachev
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import Customer
from .forms import CustomerForm


def is_manager(user):
    if user.is_superuser:
        return True
    return user.is_authenticated and user.role in ['admin', 'director', 'manager']


@login_required
@user_passes_test(is_manager)
def customer_list(request):
    customers = Customer.objects.filter(is_active=True)
    
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(short_name__icontains=search) |
            Q(inn__icontains=search) |
            Q(contact_person__icontains=search)
        )
    
    context = {
        'customers': customers,
        'active_menu': 'customers',
        'title': 'Контрагенты',
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
@user_passes_test(is_manager)
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {
        'customer': customer,
        'active_menu': 'customers',
        'title': str(customer),
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
@user_passes_test(is_manager)
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Контрагент "{customer.name}" успешно создан!')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'Добавление контрагента',
        'active_menu': 'customers',
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@user_passes_test(is_manager)
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Контрагент "{customer.name}" успешно обновлён!')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Редактирование контрагента {customer.name}',
        'active_menu': 'customers',
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@user_passes_test(is_manager)
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, f'Контрагент "{customer.name}" удалён!')
        return redirect('customers:customer_list')
    
    context = {
        'customer': customer,
        'title': f'Удаление контрагента {customer.name}',
        'active_menu': 'customers',
    }
    return render(request, 'customers/customer_confirm_delete.html', context)