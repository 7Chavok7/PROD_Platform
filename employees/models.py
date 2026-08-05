# .employees/models.py | A.Grachev
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Department(models.Model):
    """Участок / Цех"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код'
    )
    head = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='Руководитель'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Чем занимается участок, особенности'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата редактирования'
    )
    
    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'
        ordering= ['name']
        
    def __str__(self):
        return f'{self.name} ({self.code})'
    

class Skill(models.Model):
    """Квалификация / Навык"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Категория'
    )
    
    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    
class Position(models.Model):
    """Должности"""
    name = models.CharField(
        max_length=50,
        verbose_name='Наименование должности'    
    )
    code = models.CharField(
        max_length=6,
        verbose_name='Код должности',
        help_text='Максимум 6 символов. Например ОС-001'
    )
    
    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['name']
        
    def __str__(self):
        return self.name
        

class Employee(models.Model):
    """Сотрудник"""
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активен'
        VACATION = 'vacation', 'Отпуск'
        SICK = 'sick', 'Больничный'
        FIRED = 'fired', 'Уволен'
        
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee',
        verbose_name='Пользователь'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Фамилия'
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name='Имя'
    )
    patronymic = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Отчество'
    )
    personal_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Табельный номер'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Участок'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Должность'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Телефон'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата приема'
    )
    skill = models.ManyToManyField(
        Skill,
        through = 'EmployeeSkill',
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Навыки'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата редактирования'
    )
    
    class Meta:
        verbose_name = 'Сотрудник',
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']
        
    def __str__(self):
        if self.patronymic:
            return f'{self.last_name} {self.first_name} {self.patronymic}'
        return f'{self.last_name} {self.first_name}'
    
    def short_name(self):
        if self.patronymic:
            return f'{self.last_name} {self.first_name[:1]}.{self.patronymic[:1]}.'
        return f'{self.last_name} {self.first_name[:1]}.'
        
        
class EmployeeSkill(models.Model):
    """Связь сотрудника с навыком (с уровнем)"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
    )
    level = models.PositiveSmallIntegerField(
        default=1,
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name='Уровень владения'
    )
    
    class Meta:
        unique_together = [['employee', 'skill']]
        verbose_name = 'Навык сотрудника'
        verbose_name_plural = 'Навыки сотрудников'
        
    def __str__(self):
        return f'{self.employee.short_name} - {self.skill.name} (ур. {self.level})'