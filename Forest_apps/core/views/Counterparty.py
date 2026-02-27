from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Counterparty, Position
from Forest_apps.core.forms.counterparty import CounterpartyCreateForm, CounterpartyEditForm


@login_required
def counterparty_list_view(request):
    """Страница со списком контрагентов (только для должности пользователя)"""

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

    # Получаем контрагентов, созданных этой должностью
    counterparties = Counterparty.objects.filter(
        created_by_position_id=user_position_id
    ).order_by('-created_at')

    context = {
        'title': 'Контрагенты',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'counterparties': counterparties,
    }
    return render(request, 'Counterparty/counterparty_list.html', context)


@login_required
def counterparty_create_view(request):
    """Создание нового контрагента"""

    if request.method == 'POST':
        form = CounterpartyCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем контрагента
            counterparty = form.save(commit=False)

            # Добавляем создателя (пользователя)
            counterparty.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                counterparty.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                counterparty.created_by_position = position

            counterparty.save()

            messages.success(
                request,
                f'Контрагент "{counterparty.name}" успешно создан!'
            )

            return redirect('core:counterparty_list')
    else:
        form = CounterpartyCreateForm()

    context = {
        'title': 'Создание контрагента',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Counterparty/counterparty_create.html', context)


@login_required
def counterparty_edit_view(request, counterparty_id):
    """Редактирование контрагента (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:counterparty_list')

    # Получаем контрагента по ID и проверяем, что он создан этой должностью
    counterparty = get_object_or_404(
        Counterparty,
        id=counterparty_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = CounterpartyEditForm(request.POST, instance=counterparty)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Контрагент "{counterparty.name}" успешно обновлен!'
            )
            return redirect('core:counterparty_list')
    else:
        form = CounterpartyEditForm(instance=counterparty)

    context = {
        'title': 'Редактирование контрагента',
        'form': form,
        'counterparty': counterparty,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Counterparty/counterparty_edit.html', context)


@login_required
def counterparty_deactivate_view(request, counterparty_id):
    """Деактивация контрагента (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:counterparty_list')

    try:
        # Проверяем, что контрагент создан этой должностью
        counterparty = get_object_or_404(
            Counterparty,
            id=counterparty_id,
            created_by_position=position
        )
        counterparty = Counterparty.deactivate_counterparty(counterparty_id)
        messages.success(
            request,
            f'Контрагент "{counterparty.name}" успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:counterparty_list')