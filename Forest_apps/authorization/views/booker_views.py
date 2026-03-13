from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q, Sum
from Forest_apps.inventory.models import MaterialBalance, StorageLocation, MaterialMovement
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Position, Warehouse, Brigade, Vehicle
from Forest_apps.employees.models import Employee
from Forest_apps.inventory.forms.material_balance import MaterialBalanceFilterForm
from Forest_apps.inventory.forms.material_movement import MaterialMovementFilterForm


@login_required
def booker_dashboard(request):
    """Панель бухгалтера"""
    context = {
        'title': 'Панель бухгалтера',
        'employee_name': request.session.get('employee_name'),
        'position': request.session.get('position_name'),
    }
    return render(request, 'Management/booker.html', context)


@login_required
def booker_balances_view(request):
    """Страница остатков материалов для бухгалтера (доступ ко всем остаткам)"""

    # Проверяем, что пользователь - бухгалтер (или руководитель в режиме подмены)
    current_position = request.session.get('position_name', '').lower()
    if current_position not in ['бухгалтер', 'руководитель'] and not request.session.get('is_switched', False):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('authorization:login')

    # Получаем все руководящие должности (кроме руководителя)
    руководящие_должности = [
        'бухгалтер', 'механик', 'мастер леса', 'мастер ЛПЦ', 'мастер ДОЦ', 'мастер ЖД'
    ]

    # Получаем все должности для фильтра
    positions = Position.objects.filter(name__in=руководящие_должности, is_active=True)

    # Получаем все остатки с связанными данными
    balances = MaterialBalance.objects.select_related(
        'storage_location', 'material', 'created_by_position'
    ).order_by('storage_location__source_type', 'material__material_type', 'material__name')

    # Фильтрация
    filter_form = MaterialBalanceFilterForm(request.GET or None)

    if filter_form.is_valid():
        storage_location = filter_form.cleaned_data.get('storage_location')
        material_type = filter_form.cleaned_data.get('material_type')
        material = filter_form.cleaned_data.get('material')
        search = filter_form.cleaned_data.get('search')

        if storage_location:
            balances = balances.filter(storage_location=storage_location)

        if material_type:
            balances = balances.filter(material__material_type=material_type)

        if material:
            balances = balances.filter(material=material)

        if search:
            balances = balances.filter(
                Q(material__name__icontains=search) |
                Q(storage_location__source_type__icontains=search) |
                Q(storage_location__source_id__icontains=search)
            )

    # Фильтр по должности создателя места хранения
    position_id = request.GET.get('position')
    if position_id:
        position = Position.objects.filter(id=position_id).first()
        if position:
            # Находим все места хранения, созданные этой должностью
            from Forest_apps.inventory.models import StorageLocation

            # Склады, созданные этой должностью
            warehouses = Warehouse.objects.filter(created_by_position_id=position_id)
            warehouse_locations = []
            for wh in warehouses:
                try:
                    location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
                    warehouse_locations.append(location.id)
                except StorageLocation.DoesNotExist:
                    pass

            # Бригады, созданные этой должностью
            brigades = Brigade.objects.filter(created_by_position_id=position_id)
            brigade_locations = []
            for br in brigades:
                try:
                    location = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
                    brigade_locations.append(location.id)
                except StorageLocation.DoesNotExist:
                    pass

            # Транспорт, созданный этой должностью
            vehicles = Vehicle.objects.filter(created_by_position_id=position_id)
            vehicle_locations = []
            for vh in vehicles:
                try:
                    location = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
                    vehicle_locations.append(location.id)
                except StorageLocation.DoesNotExist:
                    pass

            # Объединяем все ID мест хранения
            location_ids = warehouse_locations + brigade_locations + vehicle_locations
            if location_ids:
                balances = balances.filter(storage_location_id__in=location_ids)

    # Подсчет итогов
    total_pieces = balances.aggregate(total=Sum('quantity_pieces'))['total'] or 0
    total_meters = balances.aggregate(total=Sum('quantity_meters'))['total'] or 0
    total_cubic = balances.aggregate(total=Sum('quantity_cubic'))['total'] or 0

    # Статистика по типам мест хранения
    stats_by_type = {
        'склад': balances.filter(storage_location__source_type='склад').count(),
        'автомобиль': balances.filter(storage_location__source_type='автомобиль').count(),
        'контрагент': balances.filter(storage_location__source_type='контрагент').count(),
        'бригады': balances.filter(storage_location__source_type='бригады').count(),
    }

    context = {
        'title': 'Остатки материалов',
        'employee_name': request.session.get('employee_name'),
        'position_name': request.session.get('position_name'),
        'balances': balances,
        'filter_form': filter_form,
        'positions': positions,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
        'stats_by_type': stats_by_type,
        'selected_position': position_id,
    }

    return render(request, 'Management/booker_menu/balances.html', context)


@login_required
def booker_movements_view(request):
    """Страница движений материалов для бухгалтера (доступ ко всем движениям)"""

    # Проверяем, что пользователь - бухгалтер (или руководитель в режиме подмены)
    current_position = request.session.get('position_name', '').lower()
    if current_position not in ['бухгалтер', 'руководитель'] and not request.session.get('is_switched', False):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('authorization:login')

    # Получаем все руководящие должности (кроме руководителя)
    руководящие_должности = [
        'бухгалтер', 'механик', 'мастер леса', 'мастер ЛПЦ', 'мастер ДОЦ', 'мастер ЖД'
    ]

    # Получаем все должности для фильтра
    positions = Position.objects.filter(name__in=руководящие_должности, is_active=True)

    # Получаем все движения
    movements = MaterialMovement.objects.select_related(
        'from_location', 'to_location', 'material', 'employee', 'vehicle',
        'created_by', 'created_by_position'
    ).order_by('-date_time')

    # Фильтрация
    filter_form = MaterialMovementFilterForm(request.GET or None)

    if filter_form.is_valid():
        accounting_type = filter_form.cleaned_data.get('accounting_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        from_location = filter_form.cleaned_data.get('from_location')
        to_location = filter_form.cleaned_data.get('to_location')
        material = filter_form.cleaned_data.get('material')
        is_completed = filter_form.cleaned_data.get('is_completed')
        search = filter_form.cleaned_data.get('search')

        if accounting_type:
            movements = movements.filter(accounting_type=accounting_type)

        if date_from:
            movements = movements.filter(date_time__date__gte=date_from)

        if date_to:
            movements = movements.filter(date_time__date__lte=date_to)

        if from_location:
            movements = movements.filter(from_location=from_location)

        if to_location:
            movements = movements.filter(to_location=to_location)

        if material:
            movements = movements.filter(material=material)

        if is_completed == 'true':
            movements = movements.filter(is_completed=True)
        elif is_completed == 'false':
            movements = movements.filter(is_completed=False)

        if search:
            movements = movements.filter(
                Q(material__name__icontains=search) |
                Q(from_location__source_type__icontains=search) |
                Q(to_location__source_type__icontains=search) |
                Q(from_location__source_id__icontains=search) |
                Q(to_location__source_id__icontains=search)
            )

    # Фильтр по должности создателя
    creator_position_id = request.GET.get('creator_position')
    if creator_position_id:
        movements = movements.filter(created_by_position_id=creator_position_id)

    # Подсчет статистики
    total_count = movements.count()
    total_amount = movements.filter(accounting_type='Реализация').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    pending_count = movements.filter(is_completed=False).count()

    context = {
        'title': 'Движения материалов',
        'employee_name': request.session.get('employee_name'),
        'position_name': request.session.get('position_name'),
        'movements': movements,
        'filter_form': filter_form,
        'positions': positions,
        'total_count': total_count,
        'total_amount': total_amount,
        'pending_count': pending_count,
        'selected_creator_position': creator_position_id,
    }

    return render(request, 'Management/booker_menu/movements.html', context)