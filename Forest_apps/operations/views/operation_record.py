from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from Forest_apps.operations.models import OperationRecord, OperationType
from Forest_apps.core.models import Position, Warehouse
from Forest_apps.forestry.models import Material
from Forest_apps.operations.forms.operation_record import (
    OperationRecordCreateForm,
    OperationRecordFilterForm
)
from Forest_apps.inventory.services import StorageLocationService


@login_required
def operation_record_list_view(request):
    """Список записей операций"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')

    # Получаем склады пользователя через сервис
    user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(
        user_position_name
    )
    user_warehouse_ids = [loc.source_id for loc in user_warehouses if loc.source_id]

    # Базовый запрос - операции на складах пользователя
    records = OperationRecord.objects.filter(
        warehouse_id__in=user_warehouse_ids
    ).select_related(
        'operation_type', 'warehouse', 'material', 'created_by_position'
    ).order_by('-date_time')

    # Фильтрация
    filter_form = OperationRecordFilterForm(request.GET or None, position_name=user_position_name)

    if filter_form.is_valid():
        operation_type = filter_form.cleaned_data.get('operation_type')
        warehouse = filter_form.cleaned_data.get('warehouse')
        material = filter_form.cleaned_data.get('material')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        has_measurements = filter_form.cleaned_data.get('has_measurements')

        if operation_type:
            records = records.filter(operation_type=operation_type)

        if warehouse:
            records = records.filter(warehouse=warehouse)

        if material:
            records = records.filter(material=material)

        if date_from:
            records = records.filter(date_time__date__gte=date_from)

        if date_to:
            records = records.filter(date_time__date__lte=date_to)

        if search:
            records = records.filter(
                Q(material__name__icontains=search) |
                Q(operation_type__name__icontains=search)
            )

        # Фильтр по наличию измерений
        if has_measurements == 'with_square':
            records = records.filter(square_meters__isnull=False, square_meters__gt=0)
        elif has_measurements == 'with_cubic':
            records = records.filter(cubic_meters__isnull=False, cubic_meters__gt=0)
        elif has_measurements == 'with_both':
            records = records.filter(
                square_meters__isnull=False, square_meters__gt=0,
                cubic_meters__isnull=False, cubic_meters__gt=0
            )

    # Статистика
    total_count = records.count()
    total_quantity = records.aggregate(total=Sum('quantity'))['total'] or 0
    total_square = records.aggregate(total=Sum('square_meters'))['total'] or 0
    total_cubic = records.aggregate(total=Sum('cubic_meters'))['total'] or 0

    # Статистика по типам операций
    stats_by_type = []
    for op_type in OperationType.objects.filter(is_active=True):
        type_records = records.filter(operation_type=op_type)
        type_count = type_records.count()
        type_quantity = type_records.aggregate(total=Sum('quantity'))['total'] or 0
        if type_count > 0:
            stats_by_type.append({
                'name': op_type.name,
                'count': type_count,
                'quantity': type_quantity
            })

    context = {
        'title': 'Учет операций',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'records': records,
        'filter_form': filter_form,
        'total_count': total_count,
        'total_quantity': total_quantity,
        'total_square': total_square,
        'total_cubic': total_cubic,
        'stats_by_type': stats_by_type,
    }

    return render(request, 'OperationRecord/operation_record_list.html', context)


@login_required
def operation_record_create_view(request):
    """Создание новой записи операции"""

    # Получаем должность пользователя из сессии
    position_name = request.session.get('position_name')

    if request.method == 'POST':
        form = OperationRecordCreateForm(request.POST, user=request.user, position_name=position_name)
        if form.is_valid():
            # Сохраняем запись
            record = form.save(commit=False)
            record.created_by = request.user

            # Добавляем должность создателя
            try:
                position = Position.objects.get(name__iexact=position_name)
                record.created_by_position = position
            except Position.DoesNotExist:
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                record.created_by_position = position

            record.save()

            messages.success(
                request,
                f'✅ Запись операции "{record.operation_type.name}" на {record.quantity} шт успешно создана!'
            )

            return redirect('operations:operation_record_list')
    else:
        form = OperationRecordCreateForm(user=request.user, position_name=position_name)

        # Проверяем, есть ли у пользователя склады
        user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(position_name)
        if user_warehouses.count() == 0:
            messages.warning(
                request,
                '⚠️ У вас нет складов для учета операций. Сначала создайте склад.'
            )

        # Проверяем, есть ли активные типы операций
        if form.fields['operation_type'].queryset.count() == 0:
            messages.warning(
                request,
                '⚠️ Нет активных типов операций. Сначала создайте тип операции.'
            )

    context = {
        'title': 'Создание записи операции',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'OperationRecord/operation_record_create.html', context)


@login_required
def operation_record_edit_view(request, record_id):
    """Редактирование записи операции"""

    record = get_object_or_404(
        OperationRecord.objects.select_related('operation_type', 'warehouse', 'material'),
        id=record_id
    )

    # Получаем должность пользователя
    position_name = request.session.get('position_name')

    # Проверяем, что склад принадлежит пользователю через сервис
    user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(position_name)
    user_warehouse_ids = [loc.source_id for loc in user_warehouses if loc.source_id]

    if record.warehouse.id not in user_warehouse_ids:
        messages.error(request, 'Вы можете редактировать только операции на своих складах')
        return redirect('operations:operation_record_list')

    if request.method == 'POST':
        form = OperationRecordCreateForm(request.POST, instance=record, user=request.user, position_name=position_name)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'✅ Запись операции успешно обновлена!'
            )
            return redirect('operations:operation_record_list')
    else:
        form = OperationRecordCreateForm(instance=record, user=request.user, position_name=position_name)

    context = {
        'title': f'Редактирование операции',
        'form': form,
        'record': record,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'OperationRecord/operation_record_create.html', context)


@login_required
def operation_record_delete_view(request, record_id):
    """Удаление записи операции"""

    record = get_object_or_404(OperationRecord, id=record_id)

    # Получаем должность пользователя
    position_name = request.session.get('position_name')

    # Проверяем, что склад принадлежит пользователю через сервис
    user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(position_name)
    user_warehouse_ids = [loc.source_id for loc in user_warehouses if loc.source_id]

    if record.warehouse.id not in user_warehouse_ids:
        messages.error(request, 'Вы можете удалять только операции на своих складах')
        return redirect('operations:operation_record_list')

    try:
        record.delete()
        messages.success(request, '✅ Запись операции успешно удалена!')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {str(e)}')

    return redirect('operations:operation_record_list')


@login_required
def operation_record_detail_view(request, record_id):
    """Детальный просмотр записи операции"""

    record = get_object_or_404(
        OperationRecord.objects.select_related(
            'operation_type', 'warehouse', 'material', 'created_by', 'created_by_position'
        ),
        id=record_id
    )

    context = {
        'title': f'Операция: {record.operation_type.name}',
        'employee_name': request.session.get('employee_name'),
        'record': record,
    }

    return render(request, 'OperationRecord/operation_record_detail.html', context)


@login_required
def get_operation_stats(request):
    """API для получения статистики по операциям (для графиков)"""
    from django.http import JsonResponse
    from django.db.models import Count, Sum
    from datetime import timedelta

    position_name = request.session.get('position_name')

    # Получаем склады пользователя через сервис
    user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(position_name)
    user_warehouse_ids = [loc.source_id for loc in user_warehouses if loc.source_id]

    # Статистика за последние 30 дней
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    records = OperationRecord.objects.filter(
        warehouse_id__in=user_warehouse_ids,
        date_time__date__gte=start_date,
        date_time__date__lte=end_date
    )

    # По дням
    daily_stats = records.extra(
        select={'day': "date(date_time)"}
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('quantity')
    ).order_by('day')

    # По типам операций
    type_stats = records.values(
        'operation_type__name'
    ).annotate(
        count=Count('id'),
        total=Sum('quantity')
    ).order_by('-total')

    # По материалам
    material_stats = records.values(
        'material__name',
        'material__unit'
    ).annotate(
        total=Sum('quantity')
    ).order_by('-total')[:10]

    data = {
        'daily': list(daily_stats),
        'by_type': list(type_stats),
        'top_materials': list(material_stats),
    }

    return JsonResponse(data)