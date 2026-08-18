# orders/forms.py | A.Grachev
from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model
from .models import Order, Stage, Drawing, OrderFile

User = get_user_model()


# =========================================================
# =   ФОРМА ДЛЯ ЗАКАЗА (АДАПТИВНАЯ)                       =
# =========================================================
class OrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа"""
    
    order_files = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Файлы заказа'
    )
    
    # Динамическое поле "Ответственный менеджер" — используем User
    responsible_manager = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).exclude(is_superuser=True),
        required=True,
        label='Ответственный менеджер',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Order
        fields = [
            'name', 'responsible_manager',
            'status', 'priority',
            'planned_completion_date', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'planned_completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        
        # Условно добавляем поле customer
        if apps.is_installed('customers'):
            from customers.models import Customer
            self.fields['customer'] = forms.ModelChoiceField(
                queryset=Customer.objects.filter(is_active=True),
                required=False,
                label='Заказчик',
                widget=forms.Select(attrs={'class': 'form-select'})
            )
        else:
            # Если customers не активен — делаем текстовое поле
            self.fields['customer'] = forms.CharField(
                required=False,
                label='Заказчик (название)',
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
    
    def save(self, commit=True):
        order = super().save(commit=False)
        
        # Обработка customer в зависимости от типа
        customer_data = self.cleaned_data.get('customer')
        if customer_data:
            if isinstance(customer_data, str):
                # Если это текст — сохраняем в description
                order.description = f"Заказчик: {customer_data}\n\n{order.description or ''}"
            else:
                # Если это объект Customer
                order.customer = customer_data
        
        if commit:
            order.save()
            self.save_m2m()
            
            # Сохраняем файлы
            files = self.cleaned_data.get('order_files')
            if files:
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
                    OrderFile.objects.create(
                        name=files.name,
                        file=files,
                        file_type=OrderFile.FileType.OTHER,
                        uploaded_by=order.responsible_manager,
                        order=order
                    )
        return order
    

# =========================================================
# =   ФОРМА ДЛЯ ЭТАПА (АДАПТИВНАЯ)                        =
# =========================================================
class StageForm(forms.ModelForm):
    """Форма для создания/редактирования этапа"""
    
    class Meta:
        model = Stage
        fields = [
            'name', 'planned_hours', 'planned_start_date', 'planned_finish_date',
            'status', 'comment', 'files'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'planned_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'planned_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planned_finish_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'files': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Условно добавляем поля из employees
        if apps.is_installed('employees'):
            from employees.models import Department, Skill, Employee
            
            self.fields['department'] = forms.ModelChoiceField(
                queryset=Department.objects.all(),
                required=False,
                label='Участок',
                widget=forms.Select(attrs={'class': 'form-select'})
            )
            self.fields['required_skill'] = forms.ModelChoiceField(
                queryset=Skill.objects.all(),
                required=False,
                label='Требуемый навык',
                widget=forms.Select(attrs={'class': 'form-select'})
            )
            self.fields['assigned_employee'] = forms.ModelChoiceField(
                queryset=Employee.objects.filter(status=Employee.Status.ACTIVE).exclude(user__is_superuser=True),
                required=False,
                label='Назначенный сотрудник',
                widget=forms.Select(attrs={'class': 'form-select'})
            )
            
            # Если выбран навык — фильтруем сотрудников
            if self.instance and self.instance.pk and self.instance.required_skill_id:
                self.fields['assigned_employee'].queryset = Employee.objects.filter(
                    status=Employee.Status.ACTIVE,
                    skills__id=self.instance.required_skill_id
                ).exclude(user__is_superuser=True).distinct()
        else:
            # Если employees не активен — делаем текстовые поля
            self.fields['department'] = forms.CharField(
                required=False,
                label='Участок (название)',
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            self.fields['required_skill'] = forms.CharField(
                required=False,
                label='Требуемый навык (название)',
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            self.fields['assigned_employee'] = forms.CharField(
                required=False,
                label='Назначенный сотрудник (ФИО)',
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )

    def save(self, commit=True):
        stage = super().save(commit=False)
        
        # Обработка полей в зависимости от типа
        for field in ['department', 'required_skill', 'assigned_employee']:
            value = self.cleaned_data.get(field)
            if value and isinstance(value, str):
                # Если это текст — сохраняем в comment
                stage.comment = f"{field}: {value}\n\n{stage.comment or ''}"
            elif value and not isinstance(value, str):
                # Если это объект — присваиваем
                setattr(stage, field, value)

        if commit:
            stage.save()
            self.save_m2m()
        return stage


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