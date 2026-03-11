from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count
from Forest_apps.operations.models import OperationType, OperationRecord
from Forest_apps.core.models import Warehouse


@login_required
def operations_home_view(request):
    """Главная страница техпроцессов"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')

    # Получаем ID складов пользователя
    user_warehouse_ids = Warehouse.objects.filter(
        created_by=request.user
    ).values_list('id', flat=True)

    # Статистика по типам операций
    operation_types_count = OperationType.objects.count()
    active_operation_types_count = OperationType.objects.filter(is_active=True).count()

    # Статистика по операциям на складах пользователя
    operations_stats = OperationRecord.objects.filter(
        warehouse_id__in=user_warehouse_ids
    ).aggregate(
        total_records=Count('id'),
        total_quantity=Sum('quantity')
    )

    operations_count = operations_stats['total_records'] or 0
    total_quantity = operations_stats['total_quantity'] or 0

    context = {
        'title': 'Техпроцессы',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'operation_types_count': operation_types_count,
        'active_operation_types_count': active_operation_types_count,
        'operations_count': operations_count,
        'total_quantity': total_quantity,
    }

    return render(request, 'operations.html', context)