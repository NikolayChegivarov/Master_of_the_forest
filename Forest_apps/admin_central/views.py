from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta

# Импортируем с префиксом Forest_apps
from Forest_apps.core.models import Position, Warehouse, Vehicle, Counterparty, Brigade
from Forest_apps.employees.models import Employee, WorkTimeRecord
from Forest_apps.forestry.models import Material, Forestry, CuttingArea, CuttingAreaContent
from Forest_apps.inventory.models import StorageLocation, MaterialMovement, MaterialBalance
from Forest_apps.operations.models import OperationType, OperationRecord


@staff_member_required
def dashboard_view(request):
    """Детальный дашборд с аналитикой"""

    # Общая статистика
    total_employees = Employee.objects.filter(is_active=True).count()
    total_materials = Material.objects.count()
    total_cutting_areas = CuttingArea.objects.filter(is_active=True).count()
    total_vehicles = Vehicle.objects.filter(is_active=True).count()

    # Лесничества с количеством лесосек
    forestries_summary = Forestry.objects.filter(is_active=True).annotate(
        cutting_area_count=Count('cuttingarea')
    ).order_by('-cutting_area_count')[:5]

    # Последние движения
    recent_movements = MaterialMovement.objects.select_related('material').order_by('-date_time')[:5]

    # Склады с количеством сотрудников
    warehouses = Warehouse.objects.filter(is_active=True).annotate(
        employee_count=Count('employee')
    ).order_by('-employee_count')

    # Последние операции
    recent_operations = OperationRecord.objects.select_related(
        'operation_type', 'material'
    ).order_by('-date_time')[:5]

    # Материалы с низким запасом
    low_stock_items = MaterialBalance.objects.filter(
        quantity_pieces__lt=10
    ).select_related('material', 'storage_location')[:10]

    # Ожидающие движения
    pending_movements = MaterialMovement.objects.filter(is_completed=False).count()

    # Статистика за сегодня
    today = timezone.now().date()
    today_operations = OperationRecord.objects.filter(
        date_time__date=today
    ).count()

    context = {
        'total_employees': total_employees,
        'total_materials': total_materials,
        'total_cutting_areas': total_cutting_areas,
        'total_vehicles': total_vehicles,
        'forestries_summary': forestries_summary,
        'recent_movements': recent_movements,
        'warehouses': warehouses,
        'recent_operations': recent_operations,
        'low_stock_items': low_stock_items,
        'pending_movements': pending_movements,
        'today_operations': today_operations,
        'django_version': '3.2+',
        'user': request.user,
    }

    return render(request, 'admin_central/dashboard.html', context)