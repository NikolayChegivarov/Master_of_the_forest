from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Warehouse, Position
from Forest_apps.core.forms.warehouse import WarehouseCreateForm, WarehouseEditForm


#----------------------ДЛЯ КОНКРЕТНОЙ ДОЛЖНОСТИ (ПРАВИЛЬНАЯ ВЕРСИЯ)-------------------
@login_required
def warehouse_list_view(request):
    """Страница со списком складов (только для должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        user_position_id = -1

    # Получаем склады, созданные этой должностью
    warehouses = Warehouse.objects.filter(
        created_by_position_id=user_position_id
    ).order_by('-id')

    context = {
        'title': 'Склады',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'warehouses': warehouses,
    }
    return render(request, 'Warehouse/warehouse_list.html', context)


@login_required
def warehouse_create_view(request):
    """Создание нового склада"""

    if request.method == 'POST':
        form = WarehouseCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем склад
            warehouse = form.save(commit=False)

            # Добавляем создателя (пользователя)
            warehouse.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                warehouse.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                warehouse.created_by_position = position

            warehouse.save()

            messages.success(
                request,
                f'Склад "{warehouse.name}" успешно создан!'
            )

            return redirect('core:warehouse_list')
    else:
        form = WarehouseCreateForm()

    context = {
        'title': 'Создание склада',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Warehouse/warehouse_create.html', context)


@login_required
def warehouse_edit_view(request, warehouse_id):
    """Редактирование склада (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:warehouse_list')

    # Получаем склад по ID и проверяем, что он создан этой должностью
    warehouse = get_object_or_404(
        Warehouse,
        id=warehouse_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = WarehouseEditForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Склад "{warehouse.name}" успешно обновлен!'
            )
            return redirect('core:warehouse_list')
    else:
        form = WarehouseEditForm(instance=warehouse)

    context = {
        'title': 'Редактирование склада',
        'form': form,
        'warehouse': warehouse,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Warehouse/warehouse_edit.html', context)


@login_required
def warehouse_deactivate_view(request, warehouse_id):
    """Деактивация склада (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:warehouse_list')

    try:
        # Проверяем, что склад создан этой должностью
        warehouse = get_object_or_404(
            Warehouse,
            id=warehouse_id,
            created_by_position=position
        )
        warehouse = Warehouse.deactivate_warehouse(warehouse_id)
        messages.success(
            request,
            f'Склад "{warehouse.name}" успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:warehouse_list')