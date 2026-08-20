# orders/services.py | A.Grachev
from django.db.models import Count, Q
from .models import Stage


class OrderProgressService:
    """Сервис для расчёта прогресса заказов"""
    
    @staticmethod
    def get_completed_stages_count(order):
        """Количество выполненных этапов"""
        return order.stages.filter(status=Stage.Status.COMPLETED).count()
    
    @staticmethod
    def get_total_stages_count(order):
        """Общее количество этапов"""
        return order.stages.count()
    
    @staticmethod
    def get_progress_percent(order):
        """Процент выполнения заказа"""
        total = order.stages.count()
        if total == 0:
            return 0
        completed = order.stages.filter(status=Stage.Status.COMPLETED).count()
        return int((completed / total) * 100)
    
    @staticmethod
    def get_stages_stats(order):
        """Статистика по этапам (для дашбордов)"""
        stats = order.stages.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status=Stage.Status.COMPLETED)),
            in_progress=Count('id', filter=Q(status=Stage.Status.IN_PROGRESS)),
            pending=Count('id', filter=Q(status=Stage.Status.PENDING)),
            defect=Count('id', filter=Q(status=Stage.Status.DEFECT)),
            problem=Count('id', filter=Q(status=Stage.Status.PROBLEM)),
        )
        return stats
    
    @staticmethod
    def get_orders_with_progress(orders_queryset):
        """Добавляет прогресс к каждому заказу в queryset"""
        for order in orders_queryset:
            order.progress = OrderProgressService.get_progress_percent(order)
            order.completed_count = OrderProgressService.get_completed_stages_count(order)
        return orders_queryset