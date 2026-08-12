# core_app/abstract_models.py / A.Grachev
from django.db import models


class BaseWorker(models.Model):
    """
    Абстрактная модель сотрудник.
    Служит основой для кадрового модуля.
    """
    full_name = models.CharField(
        max_length=255,
        verbose_name='ФИО'
    )
    short_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Краткое ФИО'
    )
    
    class Meta:
        abstract = True
        ordering = ['full_name']
        
    def __str__(self):
        return self.full_name
    
    
class BaseCustomer(models.Model):
    """
    Абстрактная модель контрагента.
    Служит основой для модуля контрагентов.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование'
    )
    
    class Meta:
        abstract = True
        ordering = ['name']
        
    def __str__(self):
        self.name
        

class BaseMaterial(models.Model):
    """
    Абстрактная модель материала.
    Служит основой для складского модуля
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование'
    )
    
    class Meta:
        abstract = True
        ordering = ['name']
        
    def __str__(self):
        return self.name