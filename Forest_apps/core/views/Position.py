from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Position
from Forest_apps.core.forms.position import PositionCreateForm, PositionEditForm


@login_required
def position_list_view(request):
    """Страница со списком должностей (общий справочник)"""

    # Получаем все активные должности (без фильтрации по создателю)
    active_positions = Position.get_active_positions()

    context = {
        'title': 'Должности',
        'employee_name': request.session.get('employee_name'),
        'positions': active_positions,
    }
    return render(request, 'Position/position_list.html', context)


@login_required
def position_create_view(request):
    """Создание новой должности (без привязки к пользователю)"""

    if request.method == 'POST':
        form = PositionCreateForm(request.POST)
        if form.is_valid():
            # Просто сохраняем, без created_by
            position = form.save()

            messages.success(
                request,
                f'Должность "{position.name}" успешно создана!'
            )

            return redirect('core:position_list')
    else:
        form = PositionCreateForm()

    context = {
        'title': 'Создание должности',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Position/position_create.html', context)


@login_required
def position_edit_view(request, position_id):
    """Редактирование должности"""

    position = get_object_or_404(Position, id=position_id)

    if request.method == 'POST':
        form = PositionEditForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Должность "{position.name}" успешно обновлена!'
            )
            return redirect('core:position_list')
    else:
        form = PositionEditForm(instance=position)

    context = {
        'title': 'Редактирование должности',
        'form': form,
        'position': position,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Position/position_edit.html', context)


@login_required
def position_deactivate_view(request, position_id):
    """Деактивация должности"""

    try:
        position = Position.deactivate_position(position_id)
        messages.success(
            request,
            f'Должность "{position.name}" успешно деактивирована!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:position_list')