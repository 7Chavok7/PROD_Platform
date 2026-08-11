from django import forms
from django.contrib.auth import get_user_model
from .models import Order, Stage, Drawing, OrderFile
from employees.models import Employee, Department, Skill
from customers.models import Customer

User = get_user_model()


# =========================================================
# =   ФОРМА ДЛЯ ЗАКАЗА                                     =
# =========================================================
class OrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа"""
    
    order_files = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Файлы заказа'
    )
    
    class Meta:
        model = Order
        fields = [
            'name', 'customer', 'status', 'priority',
            'planned_completion_date', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'planned_completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
    
    def save(self, commit=True):
        order = super().save(commit=False)
        if commit:
            order.save()
            # Сохраняем загруженные файлы
            files = self.cleaned_data.get('order_files')
            if files:
                # Если files - это список (MultipleFileInput), обрабатываем каждый
                if isinstance(files, list):
                    for f in files:
                        OrderFile.objects.create(
                            name=f.name,
                            file=f,
                            file_type=OrderFile.FileType.OTHER,
                            uploaded_by=order.responsible_manager,
                            order=order
                        )
                else:
                    # Если один файл
                    OrderFile.objects.create(
                        name=files.name,
                        file=files,
                        file_type=OrderFile.FileType.OTHER,
                        uploaded_by=order.responsible_manager,
                        order=order
                    )
        return order


# =========================================================
# =   ФОРМА ДЛЯ ЭТАПА                                      =
# =========================================================
class StageForm(forms.ModelForm):
    """Форма для создания/редактирования этапа"""
    
    assigned_employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(
            status=Employee.Status.ACTIVE
        ).exclude(user__is_superuser=True),
        required=False,
        label='Назначенный сотрудник',
        widget=forms.Select(attrs={'class': 'form-select'})
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
            'planned_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planned_finish_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'files': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.required_skill_id:
            self.fields['assigned_employee'].queryset = Employee.objects.filter(
                status=Employee.Status.ACTIVE,
                skills__id=self.instance.required_skill_id
            ).exclude(user__is_superuser=True).distinct()


# =========================================================
# =   ФОРМА ДЛЯ ЧЕРТЕЖА (DRAWING)                         =
# =========================================================
class DrawingForm(forms.ModelForm):
    """Форма для загрузки чертежа к этапу"""
    
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
    """Форма для загрузки файла к заказу"""
    
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
    """Форма для фильтрации списка заказов"""
    
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