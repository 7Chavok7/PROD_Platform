# employees/signals.py | A.Grachev
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Employee


User = get_user_model()


@receiver(post_save, sender=Employee)
def sync_user_from_employee(sender, instance, created, **kwargs):
    """
    Сигнал: после сохранения Employee обновляем данные в User.
    Если у оператора есть привязка к User - копируем ФИО и email.
    """
    
    # Если сотрудник не привязан к пользователю - выходим
    if not instance.user:
        return
    
    user = instance.user
    need_save = False
    
    # Синхронизируем ФИО
    if user.first_name != instance.first_name:
        user.first_name = instance.first_name
        need_save = True
    if user.last_name != instance.last_name:
        user.last_name = instance.last_name
        need_save = True
    
    # Синхронизация email
    if user.email != instance.email:
        user.email = instance.email
        need_save = True
        
    # Если были изменения - сохраняем пользователя
    if need_save:
        user.save()
        print(f'[Сигнал] Данные пользователя {user.username} синхронизированны с Employee {instance.last_name} {instance.first_name[:1]}')
        
# @receiver(post_save, sender=User)
# def create_employee_from_user(sender, instance, created, **kwargs):
#     """При создании пользователя — создаём анкету сотрудника (только если её нет)"""
#     if created:
#         if not hasattr(instance, 'employee'):
#             Employee.objects.create(
#                 user=instance,
#                 last_name=instance.last_name or '',
#                 first_name=instance.first_name or '',
#                 email=instance.email or '',
#                 department=None,
#                 position=None,
#                 status=Employee.Status.ACTIVE
#             )
#             print(f"[Сигнал] Создана пустая анкета для пользователя {instance.username}")