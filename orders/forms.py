# orders/forms.py
from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model
from .models import Order, Stage, Drawing, OrderFile
from customers.models import Customer

User = get_user_model()


# =========================================================
# =   ФОРМА ДЛЯ ЗАКАЗА (АДАПТИВНАЯ)                       =
# =========================================================
class OrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа"""
    
    # Динамическое поле "Ответственный менеджер"
    if apps.is_installed('employees'):
        responsible_manager = forms.ModelChoiceField(
            queryset=User.objects.filter(employee__status='active').exclude(is_superuser=True),
            required=True,
            label='Ответственный менеджер',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
    else:
        responsible_manager = forms.CharField(
            max_length=255,
            required=True,
            label='Ответственный менеджер (ФИО)',
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
    
    class Meta:
        model = Order
        fields = [
            'name', 'customer', 'responsible_manager',
            'status', 'priority',
            'planned_completion_date', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'planned_completion_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        
        if self.instance and self.instance.pk and self.instance.planned_completion_date:
            self.initial['planned_completion_date'] = self.instance.planned_completion_date.strftime('%Y-%m-%d')
    
    def save(self, commit=True):
        order = super().save(commit=False)
        
        if apps.is_installed('employees'):
            responsible_manager = self.cleaned_data.get('responsible_manager')
            if responsible_manager:
                order.responsible_manager = responsible_manager
        else:
            responsible_manager_text = self.cleaned_data.get('responsible_manager')
            if responsible_manager_text:
                order.description = f"Менеджер: {responsible_manager_text}\n\n{order.description or ''}"
        
        if commit:
            order.save()
            self.save_m2m()
        
        return order


# =========================================================
# =   ФОРМА ДЛЯ ЭТАПА (АДАПТИВНАЯ)                        =
# =========================================================
class StageForm(forms.ModelForm):
    """Форма для создания/редактирования этапа"""
    
    if apps.is_installed('employees'):
        from employees.models import Employee
        
        assigned_employee = forms.ModelChoiceField(
            queryset=Employee.objects.filter(
                status=Employee.Status.ACTIVE
            ).exclude(user__is_superuser=True),
            required=False,
            label='Назначенный сотрудник',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
    else:
        assigned_employee = forms.CharField(
            max_length=255,
            required=False,
            label='Назначенный сотрудник (ФИО)',
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
    
    class Meta:
        model = Stage
        fields = [
            'name', 'department', 'required_skill', 'assigned_employee',
            'planned_hours', 'planned_start_date', 'planned_finish_date',
            'status', 'comment', 'files'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'required_skill': forms.Select(attrs={'class': 'form-select'}),
            'planned_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'planned_start_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'planned_finish_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'files': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ Проверяем, что instance действительно Stage
        if apps.is_installed('employees'):
            from employees.models import Employee
            
            # Проверяем тип объекта
            if self.instance and isinstance(self.instance, Stage):
                # Если есть required_skill - фильтруем сотрудников
                if self.instance.required_skill_id:
                    self.fields['assigned_employee'].queryset = Employee.objects.filter(
                        status=Employee.Status.ACTIVE,
                        skill__id=self.instance.required_skill_id
                    ).exclude(user__is_superuser=True).distinct()
                
                # Подставляем даты при редактировании
                if self.instance.planned_start_date:
                    self.initial['planned_start_date'] = self.instance.planned_start_date.strftime('%Y-%m-%d')
                if self.instance.planned_finish_date:
                    self.initial['planned_finish_date'] = self.instance.planned_finish_date.strftime('%Y-%m-%d')
    
    def save(self, commit=True):
        stage = super().save(commit=False)
        
        if apps.is_installed('employees'):
            assigned_employee = self.cleaned_data.get('assigned_employee')
            if assigned_employee:
                stage.assigned_employee = assigned_employee
        else:
            assigned_employee_text = self.cleaned_data.get('assigned_employee')
            if assigned_employee_text:
                stage.comment = f"Назначенный сотрудник: {assigned_employee_text}\n\n{stage.comment or ''}"
        
        if commit:
            stage.save()
            self.save_m2m()
        return stage


# =========================================================
# =   ФОРМА ДЛЯ ЧЕРТЕЖА (DRAWING)                         =
# =========================================================
class DrawingForm(forms.ModelForm):
    class Meta:
        model = Drawing
        fields = ['name', 'file', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# =========================================================
# =   ФОРМА ДЛЯ ФАЙЛА ЗАКАЗА (OrderFile)                  =
# =========================================================
class OrderFileForm(forms.ModelForm):
    class Meta:
        model = OrderFile
        fields = ['name', 'file', 'file_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# =========================================================
# =   ФОРМА ДЛЯ ФИЛЬТРАЦИИ ЗАКАЗОВ                        =
# =========================================================
class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Все статусы')] + list(Order.Status.choices)
    PRIORITY_CHOICES = [('', 'Все приоритеты')] + list(Order.Priority.choices)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'this.form.submit()'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'this.form.submit()'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по номеру или названию...'})
    )