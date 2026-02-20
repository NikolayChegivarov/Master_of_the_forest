from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Vehicle
from Forest_apps.core.forms.vehicle import VehicleCreateForm, VehicleEditForm


@login_required
def vehicle_list_view(request):
    """Страница со списком транспортных средств"""

    # Получаем все активные ТС
    active_vehicles = Vehicle.get_active_vehicles()

    context = {
        'title': 'Транспортные средства',
        'employee_name': request.session.get('employee_name'),
        'vehicles': active_vehicles,
    }
    return render(request, 'Vehicle/vehicle_list.html', context)


@login_required
def vehicle_create_view(request):
    """Создание нового транспортного средства"""

    if request.method == 'POST':
        form = VehicleCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем ТС, но пока не коммитим
            vehicle = form.save(commit=False)
            # Добавляем создателя
            vehicle.created_by = request.user
            # Сохраняем
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
    """Редактирование транспортного средства"""

    # Получаем ТС по ID или возвращаем 404
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

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
    """Деактивация транспортного средства"""

    try:
        # Используем метод из модели
        vehicle = Vehicle.deactivate_vehicle(vehicle_id)
        messages.success(
            request,
            f'ТС {vehicle.brand} {vehicle.model} ({vehicle.license_plate}) успешно деактивировано!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:vehicle_list')