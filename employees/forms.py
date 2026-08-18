# .employee/forms.py | A.Grachev
from django import forms
from django.contrib.auth import get_user_model
from .models import Employee, Department, Skill, Position, EmployeeSkill

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    
    # Поля для создания нового пользователя
    username = forms.CharField(
        max_length=150,
        required=False,
        label='Логин (если нужно создать нового пользователя)',
        help_text='Оставьте пустым, если пользователь уже существует'
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Пароль'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Подтверждение пароля'
    )
    
    class Meta:
        model = Employee
        fields = [
            'user',
            'last_name',
            'first_name',
            'patronymic',
            'personal_number',
            'department',
            'position',
            'status',
            'phone',
            'email',
            'hire_date'
        ]
        widgets = {  # ✅ Исправлено: wedgets → widgets
            'hire_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'patronymic': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'personal_number': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'department': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'position': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'status': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control'}
            ),
            'user': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'skill': forms.SelectMultiple(
                attrs={'class': 'form-select'}
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Поле user НЕ ОБЯЗАТЕЛЬНО
        self.fields['user'].required = False
        
        # ПОКАЗЫВАЕМ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (без фильтрации)
        # (валидация будет в clean_user)
        
        # Если редактируем существующего сотрудника — показываем его логин
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['username'].help_text = 'Текущий логин: {}'.format(self.instance.user.username)
            # Если у сотрудника уже есть пользователь, скрываем поля создания
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['password_confirm'].widget = forms.HiddenInput()

    def clean_user(self):
        """Проверка: выбранный пользователь не должен быть привязан к другому сотруднику"""
        user = self.cleaned_data.get('user')
        if user:
            # Проверяем, есть ли у пользователя уже сотрудник
            existing = Employee.objects.filter(user=user)
            # Если это редактирование — исключаем текущего сотрудника
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f'Пользователь "{user.username}" уже привязан к сотруднику {existing.first()}'
                )
        return user

    def clean_personal_number(self):
        personal_number = self.cleaned_data.get('personal_number')
        if not personal_number:
            raise forms.ValidationError('Табельный номер обязателен для заполнения')
        
        # Проверяем уникальность
        if self.instance and self.instance.pk:
            if Employee.objects.filter(personal_number=personal_number).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Сотрудник с таким табельным номером уже существует')
        else:
            if Employee.objects.filter(personal_number=personal_number).exists():
                raise forms.ValidationError('Сотрудник с таким табельным номером уже существует')
        
        return personal_number

    def clean(self):
        """Валидация: либо выбран пользователь, либо создаём нового"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        user = cleaned_data.get('user')
        
        # Если выбран существующий пользователь — всё ок
        if user:
            return cleaned_data
        
        # Если пользователь не выбран и логин не введён — создаём сотрудника без пользователя
        if not username:
            return cleaned_data
        
        # Если логин введён — проверяем и создаём пользователя
        if User.objects.filter(username=username).exists():
            self.add_error('username', 'Пользователь с таким логином уже существует')
            return cleaned_data
        
        if not password:
            self.add_error('password', 'Пароль обязателен для нового пользователя')
            return cleaned_data
        
        if password != password_confirm:
            self.add_error('password_confirm', 'Пароли не совпадают')
            return cleaned_data
        
        return cleaned_data

    def save(self, commit=True):
        """Сохранение сотрудника и создание пользователя при необходимости"""
        instance = super().save(commit=False)
        
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = self.cleaned_data.get('user')
        
        # Если указан логин и не выбран существующий пользователь — создаём нового
        if username and not user:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email or ''
            )
            user.role = instance.get_user_role()
            user.save()
            instance.user = user
        
        # Явно сохраняем personal_number
        instance.personal_number = self.cleaned_data.get('personal_number')
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance
        

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            'name', 
            'code', 
            'head', 
            'comment'
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'code': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'head': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }
        

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = [
            'name', 
            'category'
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'category': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }
        
        
class EmployeeSkillForm(forms.ModelForm):
    class Meta:
        model = EmployeeSkill
        fields = ['skill', 'level']
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
        }


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = [
            'name', 
            'code',
            'access_level'
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'
            }),
            'code': forms.TextInput(
                attrs={'class': 'form-control'
            }),
            'access_level': forms.Select(attrs={
                'class': 'form-select'
            }),
        }