from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Vehicle, Position
from Forest_apps.core.forms.vehicle import VehicleCreateForm, VehicleEditForm


@login_required
def vehicle_list_view(request):
    """Страница со списком транспортных средств (только для должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        # Если должность не найдена, показываем пустой список
        user_position_id = -1

    # Получаем ТС, созданные этой должностью
    vehicles = Vehicle.objects.filter(
        created_by_position_id=user_position_id
    ).order_by('-created_at')

    context = {
        'title': 'Транспортные средства',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'vehicles': vehicles,
    }
    return render(request, 'Vehicle/vehicle_list.html', context)


@login_required
def vehicle_create_view(request):
    """Создание нового транспортного средства"""

    if request.method == 'POST':
        form = VehicleCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем ТС
            vehicle = form.save(commit=False)

            # Добавляем создателя (пользователя)
            vehicle.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                vehicle.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                vehicle.created_by_position = position

            vehicle.save()

            messages.success(
                request,
                f'ТС {vehicle.brand} {vehicle.model} ({vehicle.license_plate}) успешно создано!'
            )

            return redirect('core:vehicle_list')
    else:
        form = VehicleCreateForm()

    context = {
        'title': 'Создание ТС',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Vehicle/vehicle_create.html', context)


@login_required
def vehicle_edit_view(request, vehicle_id):
    """Редактирование транспортного средства (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:vehicle_list')

    # Получаем ТС по ID и проверяем, что оно создано этой должностью
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = VehicleEditForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'ТС {vehicle.brand} {vehicle.model} ({vehicle.license_plate}) успешно обновлено!'
            )
            return redirect('core:vehicle_list')
    else:
        form = VehicleEditForm(instance=vehicle)

    context = {
        'title': 'Редактирование ТС',
        'form': form,
        'vehicle': vehicle,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Vehicle/vehicle_edit.html', context)


@login_required
def vehicle_deactivate_view(request, vehicle_id):
    """Деактивация транспортного средства (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:vehicle_list')

    try:
        # Проверяем, что ТС создано этой должностью
        vehicle = get_object_or_404(
            Vehicle,
            id=vehicle_id,
            created_by_position=position
        )
        vehicle = Vehicle.deactivate_vehicle(vehicle_id)
        messages.success(
            request,
            f'ТС {vehicle.brand} {vehicle.model} ({vehicle.license_plate}) успешно деактивировано!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:vehicle_list')