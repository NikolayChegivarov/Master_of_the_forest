from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Warehouse
from Forest_apps.core.forms.warehouse import WarehouseCreateForm, WarehouseEditForm


@login_required
def warehouse_list_view(request):
    """Страница со списком складов"""

    # Получаем все активные склады
    active_warehouses = Warehouse.get_active_warehouses()

    context = {
        'title': 'Склады',
        'employee_name': request.session.get('employee_name'),
        'warehouses': active_warehouses,
    }
    # ИСПРАВЛЕНО: убрали core/ из пути
    return render(request, 'Warehouse/warehouse_list.html', context)


@login_required
def warehouse_create_view(request):
    """Создание нового склада"""

    if request.method == 'POST':
        form = WarehouseCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем склад, но пока не коммитим
            warehouse = form.save(commit=False)
            # Добавляем создателя
            warehouse.created_by = request.user
            # Сохраняем
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
    """Редактирование склада"""

    # Получаем склад по ID или возвращаем 404
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)

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

    # ИСПРАВЛЕНО: убрали core/ из пути
    return render(request, 'Warehouse/warehouse_edit.html', context)


@login_required
def warehouse_deactivate_view(request, warehouse_id):
    """Деактивация склада"""

    try:
        # Используем метод из модели
        warehouse = Warehouse.deactivate_warehouse(warehouse_id)
        messages.success(
            request,
            f'Склад "{warehouse.name}" успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:warehouse_list')