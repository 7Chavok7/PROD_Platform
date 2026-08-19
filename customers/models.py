# customers/models.py | A.Grachev
from django.db import models
from simple_history.models import HistoricalRecords


class Customer(models.Model):
    """Контрагент/заказчик"""
    class Type(models.TextChoices):
        IND_PERSON = 'ind_person', 'Физическое лицо'
        LEGAL = 'legal', 'Юридическое лицо'
        SOLE_PR = 'sole_pr', 'ИП'
        SELF_EMP = 'self_emp', 'Самозанятый'
        
    # Основные данные
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование'
    )
    short_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Краткое наименование'
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.LEGAL,
        verbose_name='Тип'
    )
    inn = models.CharField(
        max_length=12,
        blank=True,
        verbose_name='ИНН'
    )
    kpp = models.CharField(
        max_length=9,
        blank=True,
        verbose_name='КПП'
    )
    ogrn = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='ОГРН'
    )
    
    # Контакты
    contact_person = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Контактное лицо'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Юридический адрес'
    )
    actual_address = models.TextField(
        blank=True,
        verbose_name='Фактический адрес'
    )
    
    # Банковские реквизиты
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Банк'
    )
    bik = models.CharField(
        max_length=9,
        blank=True,
        verbose_name='БИК'
    )
    checking_account = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Расчетный счет'
    )
    cor_account = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Кор. счет'
    )
    
    # Дополнительно
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
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
    history = HistoricalRecords(
        verbose_name='История изменений'
    )
    
    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'
        ordering = ['name']
        
    def __str__(self):
        return self.name