from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from Forest_apps.inventory.models import MaterialMovement  # Только эта модель импортируется напрямую
from Forest_apps.inventory.forms.material_movement import (
    MaterialMovementCreateForm,
    MaterialMovementFilterForm
)


@login_required
def material_movement_list_view(request):
    """Список движений материалов"""

    # Базовый запрос
    movements = MaterialMovement.objects.select_related(
        'from_location', 'to_location', 'material', 'employee', 'vehicle', 'author'
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

    # Подсчет статистики
    total_count = movements.count()
    total_amount = movements.filter(accounting_type='Реализация').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    pending_count = movements.filter(is_completed=False).count()

    context = {
        'title': 'Движение материалов',
        'employee_name': request.session.get('employee_name'),
        'movements': movements,
        'filter_form': filter_form,
        'total_count': total_count,
        'total_amount': total_amount,
        'pending_count': pending_count,
    }

    return render(request, 'MaterialMovement/material_movement_list.html', context)


@login_required
def material_movement_create_view(request):
    """Создание нового движения материалов"""

    if request.method == 'POST':
        form = MaterialMovementCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем движение, но пока не коммитим
            movement = form.save(commit=False)
            movement.author = request.user
            movement.save()

            messages.success(
                request,
                f'Движение №{movement.id} успешно создано!'
            )

            return redirect('inventory:material_movement_list')
    else:
        form = MaterialMovementCreateForm()

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
            'from_location', 'to_location', 'material', 'employee', 'vehicle', 'author'
        ),
        id=movement_id
    )

    context = {
        'title': f'Движение №{movement.id}',
        'employee_name': request.session.get('employee_name'),
        'movement': movement,
    }

    return render(request, 'MaterialMovement/material_movement_detail.html', context)


@login_required
def material_movement_execute_view(request, movement_id):
    """Выполнение движения (проводка)"""

    try:
        movement = get_object_or_404(MaterialMovement, id=movement_id)

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
    """Отмена выполнения движения"""

    try:
        movement = get_object_or_404(MaterialMovement, id=movement_id)

        if not movement.is_completed:
            messages.error(request, 'Движение еще не выполнено')
        else:
            movement.cancel_movement()
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
def material_movement_delete_view(request, movement_id):
    """Удаление движения"""

    try:
        movement = get_object_or_404(MaterialMovement, id=movement_id)

        if movement.is_completed:
            messages.error(request, 'Нельзя удалить выполненное движение')
        else:
            movement.delete()
            messages.success(request, 'Движение успешно удалено!')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory:material_movement_list')


@login_required
def material_movement_edit_view(request, movement_id):
    """Редактирование движения"""

    movement = get_object_or_404(MaterialMovement, id=movement_id)

    if movement.is_completed:
        messages.error(request, 'Нельзя редактировать выполненное движение')
        return redirect('inventory:material_movement_detail', movement_id=movement.id)

    if request.method == 'POST':
        form = MaterialMovementCreateForm(request.POST, instance=movement)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Движение №{movement.id} успешно обновлено!'
            )
            return redirect('inventory:material_movement_detail', movement_id=movement.id)
    else:
        form = MaterialMovementCreateForm(instance=movement)

    context = {
        'title': f'Редактирование движения №{movement.id}',
        'form': form,
        'movement': movement,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'MaterialMovement/material_movement_edit.html', context)