from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from Forest_apps.operations.models import OperationType
from Forest_apps.core.models import Position
from Forest_apps.operations.forms.operation_type import (
    OperationTypeCreateForm,
    OperationTypeFilterForm
)


@login_required
def operation_type_list_view(request):
    """Список типов операций"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')

    # Базовый запрос
    operation_types = OperationType.objects.all().order_by('-is_active', 'name')

    # Фильтрация
    filter_form = OperationTypeFilterForm(request.GET or None)

    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        is_active = filter_form.cleaned_data.get('is_active')

        if search:
            operation_types = operation_types.filter(
                Q(name__icontains=search)
            )

        if is_active == 'true':
            operation_types = operation_types.filter(is_active=True)
        elif is_active == 'false':
            operation_types = operation_types.filter(is_active=False)

    # Статистика
    total_count = operation_types.count()
    active_count = operation_types.filter(is_active=True).count()
    inactive_count = operation_types.filter(is_active=False).count()

    context = {
        'title': 'Типы операций',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'operation_types': operation_types,
        'filter_form': filter_form,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }

    return render(request, 'OperationType/operation_type_list.html', context)


@login_required
def operation_type_create_view(request):
    """Создание нового типа операции"""

    if request.method == 'POST':
        form = OperationTypeCreateForm(request.POST, user=request.user)
        if form.is_valid():
            # Сохраняем тип операции
            operation_type = form.save(commit=False)

            # Добавляем создателя
            operation_type.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                operation_type.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                operation_type.created_by_position = position

            operation_type.save()

            messages.success(
                request,
                f'✅ Тип операции "{operation_type.name}" успешно создан!'
            )

            return redirect('operations:operation_type_list')
    else:
        form = OperationTypeCreateForm(user=request.user)

    context = {
        'title': 'Создание типа операции',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'OperationType/operation_type_create.html', context)


@login_required
def operation_type_edit_view(request, type_id):
    """Редактирование типа операции"""

    operation_type = get_object_or_404(OperationType, id=type_id)

    if request.method == 'POST':
        form = OperationTypeCreateForm(request.POST, instance=operation_type, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'✅ Тип операции "{operation_type.name}" успешно обновлен!'
            )
            return redirect('operations:operation_type_list')
    else:
        form = OperationTypeCreateForm(instance=operation_type, user=request.user)

    context = {
        'title': f'Редактирование: {operation_type.name}',
        'form': form,
        'operation_type': operation_type,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'OperationType/operation_type_create.html', context)


@login_required
def operation_type_toggle_active_view(request, type_id):
    """Активация/деактивация типа операции"""

    operation_type = get_object_or_404(OperationType, id=type_id)

    # Переключаем статус
    operation_type.is_active = not operation_type.is_active
    operation_type.save()

    status = "активирован" if operation_type.is_active else "деактивирован"
    messages.success(
        request,
        f'✅ Тип операции "{operation_type.name}" успешно {status}!'
    )

    return redirect('operations:operation_type_list')