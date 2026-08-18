# orders/models.py | A.Grachev
from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords


User = get_user_model()


class Order(models.Model):
    """Заказ — гибкая модель с поддержкой модулей"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Выполнен'
        CANCELLED = 'cancelled', 'Отменён'
        
    class Priority(models.TextChoices):
        HIGH = 'high', 'Высокий'
        MEDIUM = 'medium', 'Средний'
        LOW = 'low', 'Низкий'
    
    # ===== ОСНОВНЫЕ ПОЛЯ =====
    number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        verbose_name='Номер заказа'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование проекта'
    )
    
    # ===== ЗАКАЗЧИК (гибкая связь) =====
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Заказчик (название)'
    )
    customer_inn = models.CharField(
        max_length=12,
        blank=True,
        verbose_name='ИНН заказчика'
    )
    customer_contact = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Контактное лицо'
    )
    
    # ===== ОТВЕТСТВЕННЫЙ МЕНЕДЖЕР =====
    responsible_manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_orders',
        verbose_name='Ответственный менеджер'
    )
    
    # ===== СТАТУСЫ И ДАТЫ =====
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Статус'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='Приоритет'
    )
    planned_completion_date = models.DateField(
        verbose_name='Плановая дата сдачи'
    )
    actual_complition_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Фактическая дата сдачи'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    # ===== ФАЙЛЫ =====
    files = models.ManyToManyField(
        'OrderFile',
        blank=True,
        related_name='orders',
        verbose_name='Файлы заказа'
    )
    
    # ===== МЕТАДАННЫЕ =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Последние изменения'
    )
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            year = timezone.now().year
            last_order = Order.objects.filter(
                number__startswith=f'PR-{year}'
            ).order_by('number').last()
            
            if last_order:
                last_num = int(last_order.number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.number = f'PR-{year}-{new_num:04d}'
        
        # Синхронизация с Customer (если модуль активен)
        if apps.is_installed('customers') and hasattr(self, '_customer_cache'):
            try:
                if self.customer_id and not self.customer_name:
                    self.customer_name = self.customer.name
                if self.customer_id and not self.customer_inn:
                    self.customer_inn = self.customer.inn or ''
                if self.customer_id and not self.customer_contact:
                    self.customer_contact = self.customer.contact_person or ''
            except:
                pass
        
        super().save(*args, **kwargs)
    
    def get_customer_display(self):
        if apps.is_installed('customers') and self.customer_id:
            try:
                return str(self.customer)
            except:
                pass
        return self.customer_name or '—'


# УСЛОВНО добавляем поле customer, только если модуль customers активен
if apps.is_installed('customers'):
    from django.db import models
    Order.add_to_class(
        'customer',
        models.ForeignKey(
            'customers.Customer',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='orders',
            verbose_name='Заказчик (связь)'
        )
    )
    
    # Добавляем историю с excluded_fields
    Order.add_to_class(
        'history',
        HistoricalRecords(
            inherit=True,
            verbose_name='История изменений',
            excluded_fields=['customer']
        )
    )
else:
    # Если customers не активен — история без customer
    Order.add_to_class(
        'history',
        HistoricalRecords(
            inherit=True,
            verbose_name='История изменений'
        )
    )
        

class OrderFile(models.Model):
    """Файл заказа (договор, ТЗ, смета, чертежи и т.д.)"""
    class FileType(models.TextChoices):
        CONTRACT = 'contract', 'Договор'
        SPECIFICATION = 'specification', 'Техническое задание'
        DRAW = 'draw', 'Чертеж'
        ESTIMATE = 'estimate', 'Смета'
        OTHER = 'other', 'Другое'
        
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    file = models.FileField(
        upload_to='orders/%Y/%m/%d',
        verbose_name='Файл'
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
        verbose_name='Тип файла'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_order_files',
        verbose_name='Загрузил'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    history = HistoricalRecords(
        inherit=True,
        verbose_name='История изменений'
    )
    
    class Meta:
        verbose_name = 'Файл заказа'
        verbose_name_plural = 'Файлы заказов'
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f'{self.name} ({self.get_file_type_display()})'
    
    
class Stage(models.Model):
    """Этап заказа — гибкая модель с поддержкой модулей"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает назначения'
        ASSIGNED = 'assigned', 'Назначен'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Выполнен'
        DEFECT = 'defect', 'Брак'
        PROBLEM = 'problem', 'Проблема'
        ON_HOLD = 'on_hold', 'Приостановлен'
    
    # ===== СВЯЗЬ С ЗАКАЗОМ =====
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='stages',
        verbose_name='Заказ'
    )
    number = models.PositiveIntegerField(
        verbose_name='Номер этапа'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    
    # ===== ТЕКСТОВЫЕ ПОЛЯ (всегда есть) =====
    department_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Участок (название)'
    )
    required_skill_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Требуемый навык (название)'
    )
    assigned_employee_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Назначенный сотрудник (ФИО)'
    )
    
    # ===== ПЛАНОВЫЕ ДАННЫЕ =====
    planned_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Плановые часы'
    )
    planned_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Плановая дата начала'
    )
    planned_finish_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Плановая дата завершения'
    )
    
    # ===== СТАТУС =====
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    
    # ===== ФАКТИЧЕСКИЕ ДАННЫЕ =====
    actual_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Фактические часы'
    )
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Фактическая дата начала'
    )
    actual_finish_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Фактическая дата завершения'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    
    # ===== ФАЙЛЫ =====
    files = models.ManyToManyField(
        'Drawing',
        blank=True,
        related_name='stages',
        verbose_name='Чертежи'
    )
    
    # ===== МЕТАДАННЫЕ =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата изменения'
    )
    
    class Meta:
        verbose_name = 'Этап'
        verbose_name_plural = 'Этапы'
        ordering = ['order', 'number']
        unique_together = [['order', 'number']]
    
    def __str__(self):
        return f'Этап {self.number}: {self.name}'
    
    def save(self, *args, **kwargs):
        # Синхронизация с Department (если модуль активен)
        if apps.is_installed('employees') and self.department_id:
            try:
                if not self.department_name:
                    self.department_name = self.department.name
            except:
                pass
        
        # Синхронизация с Skill (если модуль активен)
        if apps.is_installed('employees') and self.required_skill_id:
            try:
                if not self.required_skill_name:
                    self.required_skill_name = self.required_skill.name
            except:
                pass
        
        # Синхронизация с Employee (если модуль активен)
        if apps.is_installed('employees') and self.assigned_employee_id:
            try:
                if not self.assigned_employee_name:
                    self.assigned_employee_name = str(self.assigned_employee)
            except:
                pass
        
        super().save(*args, **kwargs)
    
    def get_department_display(self):
        if apps.is_installed('employees') and self.department_id:
            try:
                return str(self.department)
            except:
                pass
        return self.department_name or '—'
    
    def get_skill_display(self):
        if apps.is_installed('employees') and self.required_skill_id:
            try:
                return str(self.required_skill)
            except:
                pass
        return self.required_skill_name or '—'
    
    def get_employee_display(self):
        if apps.is_installed('employees') and self.assigned_employee_id:
            try:
                return str(self.assigned_employee)
            except:
                pass
        return self.assigned_employee_name or '—'


# УСЛОВНО добавляем поля, только если модуль employees активен
if apps.is_installed('employees'):
    from django.db import models
    
    # Department
    Stage.add_to_class(
        'department',
        models.ForeignKey(
            'employees.Department',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='stages',
            verbose_name='Участок (связь)'
        )
    )
    
    # Skill
    Stage.add_to_class(
        'required_skill',
        models.ForeignKey(
            'employees.Skill',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='stages',
            verbose_name='Требуемый навык (связь)'
        )
    )
    
    # Employee
    Stage.add_to_class(
        'assigned_employee',
        models.ForeignKey(
            'employees.Employee',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='assigned_stages',
            verbose_name='Назначенный сотрудник (связь)'
        )
    )
    
    # История с excluded_fields
    Stage.add_to_class(
        'history',
        HistoricalRecords(
            inherit=True,
            verbose_name='История изменений',
            excluded_fields=['department', 'required_skill', 'assigned_employee']
        )
    )
else:
    # Если employees не активен — история без excluded_fields
    Stage.add_to_class(
        'history',
        HistoricalRecords(
            inherit=True,
            verbose_name='История изменений'
        )
    )
    
    
class Drawing(models.Model):
    """Чертежи / файлы этапа"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    file = models.FileField(
        upload_to='drawings/%Y/%m/%d',
        verbose_name='Файл'
    )
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='drawings',
        verbose_name='Файл к этапу...'
    )
    version = models.PositiveIntegerField(
        default=1,
        verbose_name='Версия'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_drawings',
        verbose_name='Загрузил'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    history = HistoricalRecords(
        inherit=True,
        verbose_name='История изменений'
    )
    
    class Meta:
        verbose_name = 'Чертеж'
        verbose_name_plural = 'Чертежи'
        ordering = ['-version']
        
    def __str__(self):
        return f'{self.name} (v{self.version})'