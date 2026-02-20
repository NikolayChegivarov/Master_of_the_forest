from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Counterparty
from Forest_apps.core.forms.counterparty import CounterpartyCreateForm, CounterpartyEditForm


@login_required
def counterparty_list_view(request):
    """Страница со списком контрагентов"""

    # Получаем все активные контрагенты
    active_counterparties = Counterparty.get_active_counterparties()

    context = {
        'title': 'Контрагенты',
        'employee_name': request.session.get('employee_name'),
        'counterparties': active_counterparties,
    }
    return render(request, 'Counterparty/counterparty_list.html', context)


@login_required
def counterparty_create_view(request):
    """Создание нового контрагента"""

    if request.method == 'POST':
        form = CounterpartyCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем контрагента, но пока не коммитим
            counterparty = form.save(commit=False)
            # Добавляем создателя
            counterparty.created_by = request.user
            # Сохраняем
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
    """Редактирование контрагента"""

    # Получаем контрагента по ID или возвращаем 404
    counterparty = get_object_or_404(Counterparty, id=counterparty_id)

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
    """Деактивация контрагента"""

    try:
        # Используем метод из модели
        counterparty = Counterparty.deactivate_counterparty(counterparty_id)
        messages.success(
            request,
            f'Контрагент "{counterparty.name}" успешно деактивирован!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:counterparty_list')