# orders/reports.py | A.Grachev
from django.db.models import Count, Sum, Q, Avg, F, Case, When, Value, FloatField, DecimalField
from django.db.models.functions import Coalesce
from datetime import timedelta
from django.utils import timezone
from .models import Order, Stage


class CustomerReports:
    """Отчеты по заказчикам"""
    
    @staticmethod
    def get_customer_orders_summary(start_date=None, end_date=None):
        """
        Отчет «Заказы по заказчикам»
        Возвращает сводку по каждому заказчику:
        - Количество заказов
        - Сумма плановых часов
        - Средняя задержка
        - Количество выполненных в срок
        - Процент выполнения в срок
        """
        # Базовый запрос
        orders = Order.objects.filter(is_deleted=False)
        
        # Фильтр по дате
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)
        
        # ✅ ИСПРАВЛЕНО: добавляем output_field для суммы
        from django.db.models import DecimalField
        
        # Группируем по заказчику
        summary = orders.values(
            'customer_id', 
            'customer__name',
            'customer__short_name',
        ).annotate(
            total_orders=Count('id'),
            total_planned_hours=Coalesce(
                Sum('stages__planned_hours', output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
            completed_orders=Count('id', filter=Q(status=Order.Status.COMPLETED)),
            overdue_orders=Count('id', filter=Q(
                status=Order.Status.IN_PROGRESS,
                planned_completion_date__lt=timezone.now().date()
            )),
        ).order_by('-total_orders')
        
        # Добавляем расчетные поля
        result = []
        for item in summary:
            # ✅ ИСПРАВЛЕНО: completion_orders → completed_orders
            completion_rate = int((item['completed_orders'] / item['total_orders'] * 100)) if item['total_orders'] > 0 else 0
            
            # Расчет средней задержки (только для выполненных заказов)
            avg_delay = Order.objects.filter(
                customer_id=item['customer_id'],
                status=Order.Status.COMPLETED,
                actual_completion_date__isnull=False,
                planned_completion_date__isnull=False,
                is_deleted=False
            ).annotate(
                delay=F('actual_completion_date') - F('planned_completion_date')
            ).aggregate(
                avg_delay=Avg('delay')
            )['avg_delay']
            
            avg_delay_days = avg_delay.days if avg_delay else 0
            
            result.append({
                'customer_id': item['customer_id'],
                'customer_name': item['customer__name'],
                'customer_short_name': item['customer__short_name'] or item['customer__name'][:20],
                'total_orders': item['total_orders'],
                'completed_orders': item['completed_orders'],
                'overdue_orders': item['overdue_orders'],
                'total_planned_hours': float(item['total_planned_hours']),
                'completion_rate': completion_rate,
                'avg_delay_days': avg_delay_days,
            })
        
        return result
    
    @staticmethod
    def get_customer_reliability(start_date=None, end_date=None):
        """
        Отчет «Надежность заказчика»
        Возвращает рейтинг заказчиков по надежности:
        - Процент заказов, выполненных в срок
        - Средняя задержка
        - Количество просроченных заказов
        """
        summary = CustomerReports.get_customer_orders_summary(start_date, end_date)
        
        # Сортируем по надежности (проценту выполнения)
        reliability = sorted(summary, key=lambda x: x['completion_rate'], reverse=True)
        
        # Добавляем рейтинг
        for idx, item in enumerate(reliability, 1):
            item['rating'] = idx
            if item['completion_rate'] >= 90:
                item['reliability_level'] = 'Высокая'
                item['reliability_color'] = 'success'
            elif item['completion_rate'] >= 70:
                item['reliability_level'] = 'Средняя'
                item['reliability_color'] = 'warning'
            else:
                item['reliability_level'] = 'Низкая'
                item['reliability_color'] = 'danger'
        
        return reliability
    
    @staticmethod
    def get_customer_detail(customer_id):
        """
        Детальный отчет по конкретному заказчику
        Возвращает список всех заказов заказчика с деталями
        """
        orders = Order.objects.filter(
            customer_id=customer_id,
            is_deleted=False
        ).select_related(
            'responsible_manager',
            'customer'
        ).prefetch_related('stages').order_by('-created_at')
        
        result = []
        for order in orders:
            total_stages = order.stages.count()
            completed_stages = order.stages.filter(status=Stage.Status.COMPLETED).count()
            
            # Проверка на просрочку
            is_overdue = (
                order.status == Order.Status.IN_PROGRESS and
                order.planned_completion_date and
                order.planned_completion_date < timezone.now().date()
            )
            
            # Фактическая задержка (если выполнен)
            delay_days = None
            if order.status == Order.Status.COMPLETED and order.actual_completion_date and order.planned_completion_date:
                delay = order.actual_completion_date - order.planned_completion_date
                delay_days = delay.days
            
            result.append({
                'order': order,
                'total_stages': total_stages,
                'completed_stages': completed_stages,
                'progress': int((completed_stages / total_stages * 100)) if total_stages > 0 else 0,
                'is_overdue': is_overdue,
                'delay_days': delay_days,
            })
        
        return result