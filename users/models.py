# .users/models.py | A.Grachev
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        DIRECTOR = 'director', 'Директор'
        MANAGER = 'manager', 'Менеджер'
        EMPLOYEE = 'employee', 'Сотрудник'
        LOGIST = 'logist', 'Логист'
        
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Роль'
    )
    
    # Наследуем все поля от AbstractUser
    # password, username, email, first_name, last_name уже есть
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username