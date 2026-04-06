from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from Forest_apps.inventory.models import MaterialBalance, StorageLocation, Receipt
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

    # НОВОЕ: Фильтрация по пустым местам хранения
    hide_empty = request.GET.get('hide_empty')
    if hide_empty:
        # Исключаем записи, где все количества равны 0
        balances = balances.exclude(
            quantity_pieces=0,
            quantity_meters=0,
            quantity_cubic=0
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
    """Создание нового остатка материала (или добавление к существующему)"""

    # Получаем должность из сессии ДО создания формы
    position_name = request.session.get('position_name')
    print(f"DEBUG view: position_name = {position_name}")  # Отладка

    if request.method == 'POST':
        form = MaterialBalanceCreateForm(request.POST, user=request.user, position_name=position_name)
        if form.is_valid():
            try:
                # Получаем должность создателя
                position = None
                if position_name:
                    try:
                        position = Position.objects.get(name__iexact=position_name)
                    except Position.DoesNotExist:
                        position, _ = Position.objects.get_or_create(
                            name=position_name,
                            defaults={'is_active': True}
                        )

                # Сохраняем форму, передавая должность и пользователя
                balance = form.save(commit=False, position=position, user=request.user)

                messages.success(
                    request,
                    f'✅ Поступление материала "{form.cleaned_data["material"].name}" '
                    f'на склад "{form.cleaned_data["storage_location"].get_source_name()}" '
                    f'успешно создано!'
                )

                return redirect('inventory:material_balance_list')

            except ValueError as e:
                messages.error(request, str(e))
                return redirect('inventory:material_balance_create')
        else:
            context = {
                'title': 'Добавление остатка',
                'form': form,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'MaterialBalance/material_balance_create.html', context)
    else:
        form = MaterialBalanceCreateForm(user=request.user, position_name=position_name)
        if form.fields['storage_location'].queryset.count() == 0:
            messages.warning(
                request,
                '⚠️ У вас нет складов для поступления материалов. Сначала создайте склад.'
            )

    context = {
        'title': 'Добавление остатка',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialBalance/material_balance_create.html', context)


@login_required
def receipt_list_view(request):
    """Список поступлений материалов"""

    user_position_name = request.session.get('position_name')

    # Получаем ID складов пользователя
    user_warehouse_ids = _get_user_warehouse_ids(request.user)

    # Поступления на склады пользователя
    receipts = Receipt.objects.filter(
        storage_location_id__in=user_warehouse_ids
    ).select_related(
        'storage_location', 'material', 'source_location', 'created_by_position'
    ).order_by('-receipt_date')

    # Статистика
    total_count = receipts.count()
    total_pieces = receipts.aggregate(total=Sum('quantity_pieces'))['total'] or 0
    total_meters = receipts.aggregate(total=Sum('quantity_meters'))['total'] or 0
    total_cubic = receipts.aggregate(total=Sum('quantity_cubic'))['total'] or 0
    total_amount = receipts.aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'title': 'Поступления материалов',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'receipts': receipts,
        'total_count': total_count,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
        'total_amount': total_amount,
    }

    return render(request, 'MaterialBalance/receipt_list.html', context)


@login_required
def receipt_edit_view(request, receipt_id):
    """Редактирование поступления"""

    receipt = get_object_or_404(
        Receipt.objects.select_related('storage_location', 'material'),
        id=receipt_id
    )

    # Проверка, что склад принадлежит пользователю
    user_warehouse_ids = _get_user_warehouse_ids(request.user)
    if receipt.storage_location.id not in user_warehouse_ids:
        messages.error(request, 'Вы можете редактировать только поступления на свои склады')
        return redirect('inventory:receipt_list')

    # Проверка, можно ли редактировать
    if not receipt.can_edit:
        messages.error(request, 'Поступление старше 5 дней, редактирование невозможно')
        return redirect('inventory:receipt_list')

    if request.method == 'POST':
        form = MaterialBalanceCreateForm(
            request.POST,
            user=request.user,
            receipt_instance=receipt  # Передаем экземпляр поступления
        )
        if form.is_valid():
            try:
                # Получаем должность создателя
                position_name = request.session.get('position_name')
                position = None
                if position_name:
                    try:
                        position = Position.objects.get(name__iexact=position_name)
                    except Position.DoesNotExist:
                        position, _ = Position.objects.get_or_create(
                            name=position_name,
                            defaults={'is_active': True}
                        )

                # Сохраняем форму, передавая должность
                balance = form.save(commit=False, position=position, user=request.user)
                messages.success(request, f'✅ Поступление №{receipt.id} успешно обновлено!')
                return redirect('inventory:receipt_list')
            except ValueError as e:
                messages.error(request, str(e))
        else:
            context = {
                'title': f'Редактирование поступления №{receipt.id}',
                'form': form,
                'receipt': receipt,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'MaterialBalance/material_balance_create.html', context)
    else:
        # GET запрос - передаем receipt_instance в форму
        form = MaterialBalanceCreateForm(
            user=request.user,
            receipt_instance=receipt
        )

    context = {
        'title': f'Редактирование поступления №{receipt.id}',
        'form': form,
        'receipt': receipt,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialBalance/material_balance_create.html', context)


@login_required
def receipt_delete_view(request, receipt_id):
    """Удаление поступления"""

    receipt = get_object_or_404(
        Receipt.objects.select_related('storage_location', 'material'),
        id=receipt_id
    )

    # Проверка, что склад принадлежит пользователю
    user_warehouse_ids = _get_user_warehouse_ids(request.user)
    if receipt.storage_location.id not in user_warehouse_ids:
        messages.error(request, 'Вы можете удалять только поступления на свои склады')
        return redirect('inventory:receipt_list')

    # Проверка, можно ли удалять
    if not receipt.can_edit:
        messages.error(request, 'Поступление старше 5 дней, удаление невозможно')
        return redirect('inventory:receipt_list')

    try:
        # Получаем баланс
        balance = MaterialBalance.objects.get(
            storage_location=receipt.storage_location,
            material=receipt.material
        )

        # Проверяем, достаточно ли остатков для удаления
        pieces_to_remove = receipt.quantity_pieces or 0
        meters_to_remove = receipt.quantity_meters or 0
        cubic_to_remove = receipt.quantity_cubic or 0

        if pieces_to_remove > 0 and balance.quantity_pieces < pieces_to_remove:
            raise ValueError(
                f'Недостаточно материала на складе. В наличии: {balance.quantity_pieces} шт, '
                f'требуется удалить: {pieces_to_remove} шт'
            )
        if meters_to_remove > 0 and (balance.quantity_meters or 0) < meters_to_remove:
            raise ValueError(
                f'Недостаточно материала на складе. В наличии: {balance.quantity_meters or 0} м.п., '
                f'требуется удалить: {meters_to_remove} м.п.'
            )
        if cubic_to_remove > 0 and (balance.quantity_cubic or 0) < cubic_to_remove:
            raise ValueError(
                f'Недостаточно материала на складе. В наличии: {balance.quantity_cubic or 0} м³, '
                f'требуется удалить: {cubic_to_remove} м³'
            )

        # Уменьшаем баланс
        balance.quantity_pieces -= pieces_to_remove
        balance.quantity_meters = (balance.quantity_meters or 0) - meters_to_remove
        balance.quantity_cubic = (balance.quantity_cubic or 0) - cubic_to_remove
        balance.save()

        # Удаляем поступление
        receipt.delete()

        messages.success(request, f'✅ Поступление №{receipt.id} успешно удалено!')

    except MaterialBalance.DoesNotExist:
        messages.error(request, f'Остаток материала не найден на складе')
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {str(e)}')

    return redirect('inventory:receipt_list')


@login_required
def receipt_detail_view(request, receipt_id):
    """Детальный просмотр поступления"""

    receipt = get_object_or_404(
        Receipt.objects.select_related(
            'storage_location', 'material', 'source_location',
            'created_by', 'created_by_position'
        ),
        id=receipt_id
    )

    context = {
        'title': f'Поступление №{receipt.id}',
        'employee_name': request.session.get('employee_name'),
        'receipt': receipt,
    }

    return render(request, 'MaterialBalance/receipt_detail.html', context)


def _get_user_warehouse_ids(user):
    """Вспомогательная функция для получения ID складов пользователя"""
    if not user or not user.is_authenticated:
        return []

    from Forest_apps.inventory.models import StorageLocation
    from Forest_apps.core.models import Warehouse

    user_warehouse_ids = []

    warehouses = Warehouse.objects.filter(created_by=user)
    for wh in warehouses:
        try:
            location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
            user_warehouse_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    return user_warehouse_ids


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