from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from Forest_apps.inventory.models import MaterialMovement, StorageLocation
from Forest_apps.core.models import Position, Warehouse, Brigade, Vehicle
from Forest_apps.inventory.forms.material_movement import (
    MaterialMovementCreateForm,
    MaterialMovementFilterForm
)


@login_required
def material_movement_list_view(request):
    """Список движений материалов (для должности пользователя как отправителя или получателя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        user_position_id = -1

    # Получаем ID мест хранения, принадлежащих этой должности
    from Forest_apps.inventory.models import StorageLocation
    from Forest_apps.core.models import Warehouse, Brigade, Vehicle

    user_location_ids = []

    # Склады, созданные должностью
    warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id)
    for wh in warehouses:
        try:
            location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Бригады, созданные должностью
    brigades = Brigade.objects.filter(created_by_position_id=user_position_id)
    for br in brigades:
        try:
            location = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Транспорт, созданный должностью
    vehicles = Vehicle.objects.filter(created_by_position_id=user_position_id)
    for vh in vehicles:
        try:
            location = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Базовый запрос - движения, где должность является отправителем ИЛИ получателем
    movements = MaterialMovement.objects.filter(
        Q(from_location_id__in=user_location_ids) |  # должность - отправитель
        Q(to_location_id__in=user_location_ids)  # должность - получатель
    ).select_related(
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
                Q(to_location__source_type__icontains=search)
            )

    # Получаем ID мест хранения текущего пользователя для проверки прав на подтверждение
    user_locations = user_location_ids  # используем тот же список

    # Подсчет ожидающих отправлений для текущего пользователя
    pending_shipments_count = MaterialMovement.get_pending_shipments_for_user(request.user).count()

    # Подсчет статистики
    total_count = movements.count()
    total_amount = movements.filter(accounting_type='Реализация').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    pending_count = movements.filter(is_completed=False).count()

    context = {
        'title': 'Движение материалов',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'movements': movements,
        'filter_form': filter_form,
        'total_count': total_count,
        'total_amount': total_amount,
        'pending_count': pending_count,
        'pending_shipments_count': pending_shipments_count,
        'user_locations': user_locations,
    }

    return render(request, 'MaterialMovement/material_movement_list.html', context)


@login_required
def material_movement_create_view(request):
    """Создание нового движения материалов"""

    if request.method == 'POST':
        form = MaterialMovementCreateForm(request.POST, user=request.user)
        if form.is_valid():
            # Сохраняем движение
            movement = form.save(commit=False)
            movement.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                movement.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                movement.created_by_position = position

            # Для Перемещения, Реализации и Списания сразу устанавливаем is_completed=True
            if movement.accounting_type in ['Перемещение', 'Реализация', 'Списание']:
                movement.is_completed = True
                movement.completed_at = timezone.now()
            else:
                movement.is_completed = False

            movement.save()

            # Если движение должно быть выполнено сразу, выполняем его
            if movement.is_completed:
                try:
                    movement.execute_movement()
                except ValueError as e:
                    # Если не хватает материалов, удаляем созданное движение
                    movement.delete()
                    messages.error(request, str(e))
                    return redirect('inventory:material_movement_create')

            messages.success(
                request,
                f'Движение №{movement.id} успешно создано!'
            )

            return redirect('inventory:material_movement_list')
    else:
        form = MaterialMovementCreateForm(user=request.user)

    context = {
        'title': 'Создание движения',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialMovement/material_movement_create.html', context)


@login_required
def material_movement_detail_view(request, movement_id):
    """Детальный просмотр движения"""

    movement = get_object_or_404(
        MaterialMovement.objects.select_related(
            'from_location', 'to_location', 'material', 'employee', 'vehicle',
            'created_by', 'created_by_position'
        ),
        id=movement_id
    )

    # Определяем роль текущего пользователя
    user_role = movement.get_user_role(request.user)

    context = {
        'title': f'Движение №{movement.id}',
        'employee_name': request.session.get('employee_name'),
        'movement': movement,
        'user_role': user_role,  # 'sender', 'receiver', или 'none'
    }

    return render(request, 'MaterialMovement/material_movement_detail.html', context)


@login_required
def material_movement_edit_view(request, movement_id):
    """Редактирование движения (только для своей должности и только невыполненных)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_movement_list')

    movement = get_object_or_404(
        MaterialMovement,
        id=movement_id,
        created_by_position=position
    )

    # Проверка на выполненное движение
    if movement.is_completed:
        messages.error(request, 'Нельзя редактировать выполненное движение')
        return redirect('inventory:material_movement_detail', movement_id=movement.id)

    # Для отправлений проверяем, что пользователь - отправитель
    if movement.accounting_type == 'Отправление':
        user_role = movement.get_user_role(request.user)
        if user_role != 'sender':
            messages.error(request, 'Только отправитель может редактировать это движение')
            return redirect('inventory:material_movement_detail', movement_id=movement.id)

    if request.method == 'POST':
        form = MaterialMovementCreateForm(request.POST, instance=movement, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Движение №{movement.id} успешно обновлено!'
            )
            return redirect('inventory:material_movement_detail', movement_id=movement.id)
    else:
        form = MaterialMovementCreateForm(instance=movement, user=request.user)

    context = {
        'title': f'Редактирование движения №{movement.id}',
        'form': form,
        'movement': movement,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialMovement/material_movement_edit.html', context)


@login_required
def material_movement_delete_view(request, movement_id):
    """Удаление движения (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_movement_list')

    try:
        movement = get_object_or_404(
            MaterialMovement,
            id=movement_id,
            created_by_position=position
        )

        if movement.is_completed:
            messages.error(request, 'Нельзя удалить выполненное движение')
        else:
            movement.delete()
            messages.success(request, 'Движение успешно удалено!')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory:material_movement_list')


@login_required
def material_movement_execute_view(request, movement_id):
    """Выполнение движения (проводка) - только для своей должности"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_movement_list')

    try:
        movement = get_object_or_404(
            MaterialMovement,
            id=movement_id,
            created_by_position=position
        )

        if movement.is_completed:
            messages.error(request, 'Движение уже выполнено')
        else:
            movement.execute_movement()
            messages.success(
                request,
                f'Движение №{movement.id} успешно выполнено!'
            )
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Ошибка при выполнении: {str(e)}')

    return redirect('inventory:material_movement_list')


@login_required
def material_movement_cancel_view(request, movement_id):
    """Отмена выполнения движения - только для своей должности"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('inventory:material_movement_list')

    try:
        movement = get_object_or_404(
            MaterialMovement,
            id=movement_id,
            created_by_position=position
        )

        if not movement.is_completed:
            messages.error(request, 'Движение еще не выполнено')
        else:
            from Forest_apps.inventory.models import MaterialBalance
            MaterialBalance.cancel_movement(movement)
            movement.is_completed = False
            movement.completed_at = None
            movement.save()
            messages.success(
                request,
                f'Выполнение движения №{movement.id} отменено!'
            )
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Ошибка при отмене: {str(e)}')

    return redirect('inventory:material_movement_list')


@login_required
def material_movement_confirm_shipment_view(request, movement_id):
    """Подтверждение получения отправления (только для получателя)"""

    try:
        movement = get_object_or_404(MaterialMovement, id=movement_id)

        if movement.accounting_type != 'Отправление':
            messages.error(request, 'Подтверждение возможно только для отправлений')
            return redirect('inventory:material_movement_list')

        if movement.is_completed:
            messages.error(request, 'Отправление уже подтверждено')
            return redirect('inventory:material_movement_list')

        # Проверяем, что пользователь - получатель
        user_role = movement.get_user_role(request.user)
        if user_role != 'receiver':
            messages.error(request, 'Только получатель может подтвердить это отправление')
            return redirect('inventory:material_movement_list')

        # Подтверждаем получение
        movement.confirm_receipt()
        messages.success(request, f'Отправление №{movement.id} успешно подтверждено!')

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Ошибка при подтверждении: {str(e)}')

    return redirect('inventory:material_movement_list')


@login_required
def material_movement_pending_shipments_view(request):
    """Список ожидающих отправлений для текущего пользователя"""

    movements = MaterialMovement.get_pending_shipments_for_user(request.user)

    context = {
        'title': 'Ожидающие отправления',
        'employee_name': request.session.get('employee_name'),
        'movements': movements,
    }

    return render(request, 'MaterialMovement/material_movement_pending.html', context)


@login_required
def get_locations_by_type(request):
    """API для получения списка мест хранения в зависимости от типа движения"""
    movement_type = request.GET.get('type')
    user = request.user

    if not movement_type:
        return JsonResponse({'from_locations': [], 'to_locations': []})

    # Получаем ID мест пользователя
    user_location_ids = _get_user_location_ids(user)

    # Базовый queryset
    from_locations = StorageLocation.objects.none()
    to_locations = StorageLocation.objects.none()

    if movement_type == 'Перемещение':
        from_locations = StorageLocation.objects.filter(id__in=user_location_ids)
        to_locations = StorageLocation.objects.filter(id__in=user_location_ids)

    elif movement_type == 'Отправление':
        from_locations = StorageLocation.objects.filter(id__in=user_location_ids)
        to_locations = StorageLocation.objects.exclude(id__in=user_location_ids).exclude(source_type='контрагент')

    elif movement_type == 'Реализация':
        from_locations = StorageLocation.objects.all()
        to_locations = StorageLocation.objects.filter(source_type='контрагент')

    elif movement_type == 'Списание':
        from_locations = StorageLocation.objects.filter(id__in=user_location_ids)
        to_locations = StorageLocation.objects.filter(source_type__in=['бригады', 'автомобиль'])

    # Убираем дубликаты и сортируем
    from_locations = from_locations.distinct().order_by('source_type')
    to_locations = to_locations.distinct().order_by('source_type')

    # Форматируем ответ
    data = {
        'from_locations': [
            {'id': loc.id, 'name': loc.get_source_name()}
            for loc in from_locations
        ],
        'to_locations': [
            {'id': loc.id, 'name': loc.get_source_name()}
            for loc in to_locations
        ]
    }

    return JsonResponse(data)


def _get_user_location_ids(user):
    """Вспомогательная функция для получения ID мест хранения пользователя"""
    if not user or not user.is_authenticated:
        return []

    from Forest_apps.inventory.models import StorageLocation
    from Forest_apps.core.models import Warehouse, Brigade, Vehicle

    user_location_ids = []

    # Склады, созданные пользователем
    warehouses = Warehouse.objects.filter(created_by=user)
    for wh in warehouses:
        try:
            location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Бригады, созданные пользователем
    brigades = Brigade.objects.filter(created_by=user)
    for br in brigades:
        try:
            location = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    # Транспорт, созданный пользователем
    vehicles = Vehicle.objects.filter(created_by=user)
    for vh in vehicles:
        try:
            location = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
            user_location_ids.append(location.id)
        except StorageLocation.DoesNotExist:
            pass

    return user_location_ids