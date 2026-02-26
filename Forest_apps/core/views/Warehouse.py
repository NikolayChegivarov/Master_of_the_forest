from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Warehouse
from Forest_apps.core.forms.warehouse import WarehouseCreateForm, WarehouseEditForm


@login_required
def warehouse_list_view(request):
    """Страница со списком складов (только свои)"""

    # Получаем только склады, созданные текущим пользователем
    warehouses = Warehouse.objects.filter(
        created_by=request.user
    ).order_by('name')

    context = {
        'title': 'Мои склады',
        'employee_name': request.session.get('employee_name'),
        'warehouses': warehouses,
    }
    return render(request, 'Warehouse/warehouse_list.html', context)


@login_required
def warehouse_create_view(request):
    """Создание нового склада"""

    if request.method == 'POST':
        form = WarehouseCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем склад с указанием создателя
            warehouse = form.save(commit=False)
            warehouse.created_by = request.user
            warehouse.save()

            messages.success(
                request,
                f'Склад "{warehouse.name}" успешно создан!'
            )

            return redirect('core:warehouse_list')
        else:
            context = {
                'title': 'Создание склада',
                'form': form,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'Warehouse/warehouse_create.html', context)
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
    """Редактирование склада (только своего)"""

    # Получаем склад по ID и проверяем, что он принадлежит пользователю
    warehouse = get_object_or_404(Warehouse, id=warehouse_id, created_by=request.user)

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
            context = {
                'title': 'Редактирование склада',
                'form': form,
                'warehouse': warehouse,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'Warehouse/warehouse_edit.html', context)
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
    """Деактивация склада (только своего)"""

    try:
        # Проверяем, что склад принадлежит пользователю
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, created_by=request.user)
        warehouse = Warehouse.deactivate_warehouse(warehouse_id)
        messages.success(
            request,
            f'Склад "{warehouse.name}" успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:warehouse_list')