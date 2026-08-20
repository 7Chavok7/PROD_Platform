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
    
    # Наследуем все поля от AbstractUser
    # password, username, email, first_name, last_name уже есть
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username
    
    def get_access_level(self):
        """Получает уровень доступа из анкеты сотрудника"""
        if hasattr(self, 'employee') and self.employee:
            return self.employee.get_access_level()
        return 'employee'
    
    def is_manager(self):
        """Проверка, имеет ли пользователь права менеджера"""
        access_level = self.get_access_level()
        return access_level in ['manager', 'director', 'admin']