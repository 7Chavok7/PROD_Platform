# orders/models.py | A.Grachev
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from employees.models import Employee
from customers.models import Customer
from simple_history.models import HistoricalRecords


User = get_user_model()


class Order(models.Model):
    """Заказ"""
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Выполнен'
        CANCELLED = 'cancelled', 'Отменён'
        
    class Priority(models.TextChoices):
        HIGH = 'high', 'Высокий'
        MEDIUM = 'medium', 'Средний'
        LOW = 'low', 'Низкий'
        
    number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False, # Запрет на ручное редактирование
        verbose_name='Номер заказа'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование проекта'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Заказчик'
    )
    responsible_manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_orders',
        verbose_name='Ответственный менеджер'
    )
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
    actual_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Фактическая дата сдачи'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    files = models.ManyToManyField(
        'OrderFile',
        blank=True,
        related_name='orders',
        verbose_name='Файлы заказа'
    )
    
    # Поля для удаления
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Удален',
        help_text='Помечен на удаление (виден только администраторам)'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата удаления'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_orders',
        verbose_name='Кто удалил'
    )
    
    # метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Последние изменения'
    )
    history = HistoricalRecords(
        inherit=True,
        verbose_name='История изменений'
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
        super().save(*args, **kwargs)
        
    def soft_delete(self, user):
        """Мягкое удаление заказа"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
        
    def restore(self):
        """Восстаноевление заказа"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
        

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
    version = models.PositiveIntegerField(
        default=1,
        verbose_name='Версия файла'
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
    
    def get_file_icon(self):
        """Возвращает иконку для типа файла"""
        icons = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'dwg': 'fa-file',
            'dxf': 'fa-file',
            'zip': 'fa-file-archive',
        }
        ext = self.name.split('.')[-1].lower()
        return icons.get(ext, 'fa-file')
    
    def detect_file_type(self):
        """Определяет тип файла по расширению"""
        ext = self.name.split('.')[-1].lower()
        mapping = {
            'pdf': self.FileType.CONTRACT,
            'doc': self.FileType.CONTRACT,
            'docx': self.FileType.CONTRACT,
            'xls': self.FileType.ESTIMATE,
            'xlsx': self.FileType.ESTIMATE,
            'dwg': self.FileType.DRAW,
            'dxf': self.FileType.DRAW,
            'jpg': self.FileType.DRAW,
            'jpeg': self.FileType.DRAW,
            'png': self.FileType.DRAW,
        }
        return mapping.get(ext, self.FileType.OTHER)
    
    
class Stage(models.Model):
    """Этап заказа"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает назначения'
        ASSIGNED = 'assigned', 'Назначен'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Выполнен'
        DEFECT = 'defect', 'Брак'
        PROBLEM = 'problem', 'Проблема'
        ON_HOLD = 'on_hold', 'Приостановлен'
        
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
    department = models.ForeignKey(
        'employees.Department',
        on_delete=models.PROTECT,
        related_name='stages',
        verbose_name='Участок'
    )
    required_skill = models.ForeignKey(
        'employees.Skill',
        on_delete=models.PROTECT,
        related_name='stages',
        verbose_name='Требуемый навык'
    )
    assigned_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_stages',
        verbose_name='Назначеный сотрудник'
    )
    planned_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Плановые часы'
    )
    planned_start_date = models.DateField(
        verbose_name='Плановая дата начала'
    )
    planned_finish_date = models.DateField(
        verbose_name='Плановая дата завершения'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
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
    files = models.ManyToManyField(
        'Drawing',
        blank=True,
        related_name='stages',
        verbose_name='Чертежи'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата изменения'
    )
    history = HistoricalRecords(
        inherit=True,
        verbose_name='История изменений'
    )
    
    class Meta:
        verbose_name = 'Этап'
        verbose_name_plural = 'Этапы'
        ordering = ['order', 'number']
        unique_together = [['order', 'number']]
        
    def __str__(self):
        return f'Этап {self.number}: {self.name}'
    
    
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