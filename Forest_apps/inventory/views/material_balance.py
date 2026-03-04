from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from Forest_apps.inventory.models import MaterialBalance, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Position, Warehouse, Brigade, Vehicle
from Forest_apps.inventory.forms.material_balance import (
    MaterialBalanceCreateForm,
    MaterialBalanceFilterForm
)


@login_required
def material_balance_list_view(request):
    """Список остатков материалов (остатки на складах должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        user_position_id = -1

    # Получаем ВСЕ места хранения, принадлежащие этой должности
    from Forest_apps.inventory.models import StorageLocation

    # Находим все ID мест хранения, созданные этой должностью
    user_storage_location_ids = []

    # Склады, созданные этой должностью
    warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id)
    for wh in warehouses:
        try:
            location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
            user_storage_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Бригады, созданные этой должностью
    brigades = Brigade.objects.filter(created_by_position_id=user_position_id)
    for br in brigades:
        try:
            location = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
            user_storage_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Транспорт, созданный этой должностью
    vehicles = Vehicle.objects.filter(created_by_position_id=user_position_id)
    for vh in vehicles:
        try:
            location = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
            user_storage_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Базовый запрос - все остатки на местах хранения этой должности
    balances = MaterialBalance.objects.filter(
        storage_location_id__in=user_storage_location_ids
    ).select_related(
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
                Q(storage_location__source_type__icontains=search)
            )

    # Получаем ID мест хранения текущего пользователя для проверки прав на редактирование
    user_warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id).values_list('id', flat=True)
    user_brigades = Brigade.objects.filter(created_by_position_id=user_position_id).values_list('id', flat=True)
    user_vehicles = Vehicle.objects.filter(created_by_position_id=user_position_id).values_list('id', flat=True)

    # Преобразуем в списки для удобства проверки в шаблоне
    user_warehouses = list(user_warehouses)
    user_brigades = list(user_brigades)
    user_vehicles = list(user_vehicles)

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
        'position_name': user_position_name,
        'balances': balances,
        'filter_form': filter_form,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
        'stats_by_type': stats_by_type,
        'user_warehouses': user_warehouses,
        'user_brigades': user_brigades,
        'user_vehicles': user_vehicles,
    }

    return render(request, 'MaterialBalance/material_balance_list.html', context)


@login_required
def material_balance_create_view(request):
    """Создание нового остатка материала (только на свои места хранения)"""

    if request.method == 'POST':
        form = MaterialBalanceCreateForm(request.POST, user=request.user)
        if form.is_valid():
            # Сохраняем остаток
            balance = form.save(commit=False)

            # Добавляем создателя (пользователя)
            balance.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                balance.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                balance.created_by_position = position

            balance.save()

            messages.success(
                request,
                f'Остаток для {balance.material.name} на {balance.storage_location.get_source_name()} успешно создан!'
            )

            return redirect('inventory:material_balance_list')
        else:
            # Если форма невалидна, показываем ее с ошибками
            context = {
                'title': 'Добавление остатка',
                'form': form,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'MaterialBalance/material_balance_create.html', context)
    else:
        form = MaterialBalanceCreateForm(user=request.user)
        # Проверяем, есть ли у пользователя свои места хранения
        if form.fields['storage_location'].queryset.count() == 0:
            messages.warning(
                request,
                'У вас нет мест хранения (складов, ТС, бригад), на которые можно создать остаток. Сначала создайте их в соответствующих разделах.'
            )

    context = {
        'title': 'Добавление остатка',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialBalance/material_balance_create.html', context)


@login_required
def material_balance_edit_view(request, balance_id):
    """Редактирование остатка материала (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_balance_list')

    balance = get_object_or_404(
        MaterialBalance,
        id=balance_id,
        created_by_position=position
    )

    # Проверяем, принадлежит ли место хранения пользователю
    from Forest_apps.core.models import Warehouse, Brigade, Vehicle

    is_owner = False
    loc = balance.storage_location

    if loc.source_type == 'склад':
        is_owner = Warehouse.objects.filter(id=loc.source_id, created_by=request.user).exists()
    elif loc.source_type == 'бригады':
        is_owner = Brigade.objects.filter(id=loc.source_id, created_by=request.user).exists()
    elif loc.source_type == 'автомобиль':
        is_owner = Vehicle.objects.filter(id=loc.source_id, created_by=request.user).exists()

    if not is_owner:
        messages.error(request, 'Вы можете редактировать только остатки на своих местах хранения')
        return redirect('inventory:material_balance_list')

    if request.method == 'POST':
        form = MaterialBalanceCreateForm(request.POST, instance=balance, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Остаток для {balance.material.name} успешно обновлен!'
            )
            return redirect('inventory:material_balance_list')
        else:
            context = {
                'title': 'Редактирование остатка',
                'form': form,
                'balance': balance,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'MaterialBalance/material_balance_edit.html', context)
    else:
        form = MaterialBalanceCreateForm(instance=balance, user=request.user)

    context = {
        'title': 'Редактирование остатка',
        'form': form,
        'balance': balance,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialBalance/material_balance_edit.html', context)


@login_required
def material_balance_delete_view(request, balance_id):
    """Удаление остатка материала (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_balance_list')

    try:
        balance = get_object_or_404(
            MaterialBalance,
            id=balance_id,
            created_by_position=position
        )

        # Проверяем, принадлежит ли место хранения пользователю
        from Forest_apps.core.models import Warehouse, Brigade, Vehicle

        is_owner = False
        loc = balance.storage_location

        if loc.source_type == 'склад':
            is_owner = Warehouse.objects.filter(id=loc.source_id, created_by=request.user).exists()
        elif loc.source_type == 'бригады':
            is_owner = Brigade.objects.filter(id=loc.source_id, created_by=request.user).exists()
        elif loc.source_type == 'автомобиль':
            is_owner = Vehicle.objects.filter(id=loc.source_id, created_by=request.user).exists()

        if not is_owner:
            messages.error(request, 'Вы можете удалять только остатки на своих местах хранения')
            return redirect('inventory:material_balance_list')

        balance.delete()
        messages.success(request, 'Остаток успешно удален!')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory:material_balance_list')


@login_required
def material_balance_detail_view(request, balance_id):
    """Детальный просмотр остатка"""

    balance = get_object_or_404(
        MaterialBalance.objects.select_related('storage_location', 'material', 'created_by_position'),
        id=balance_id
    )

    context = {
        'title': f'Остаток: {balance.material.name}',
        'employee_name': request.session.get('employee_name'),
        'balance': balance,
    }

    return render(request, 'MaterialBalance/material_balance_detail.html', context)