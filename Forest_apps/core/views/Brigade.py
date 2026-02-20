from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Brigade
from Forest_apps.core.forms.brigade import BrigadeCreateForm, BrigadeEditForm


@login_required
def brigade_list_view(request):
    """Страница со списком бригад"""

    # Получаем все активные бригады
    active_brigades = Brigade.get_active_brigades()

    context = {
        'title': 'Бригады',
        'employee_name': request.session.get('employee_name'),
        'brigades': active_brigades,
    }
    return render(request, 'Brigade/brigade_list.html', context)


@login_required
def brigade_create_view(request):
    """Создание новой бригады"""

    if request.method == 'POST':
        form = BrigadeCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем бригаду, но пока не коммитим
            brigade = form.save(commit=False)
            # Добавляем создателя
            brigade.created_by = request.user
            # Сохраняем
            brigade.save()

            messages.success(
                request,
                f'Бригада "{brigade.name}" успешно создана!'
            )

            return redirect('core:brigade_list')
    else:
        form = BrigadeCreateForm()

    context = {
        'title': 'Создание бригады',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Brigade/brigade_create.html', context)


@login_required
def brigade_edit_view(request, brigade_id):
    """Редактирование бригады"""

    # Получаем бригаду по ID или возвращаем 404
    brigade = get_object_or_404(Brigade, id=brigade_id)

    if request.method == 'POST':
        form = BrigadeEditForm(request.POST, instance=brigade)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Бригада "{brigade.name}" успешно обновлена!'
            )
            return redirect('core:brigade_list')
    else:
        form = BrigadeEditForm(instance=brigade)

    context = {
        'title': 'Редактирование бригады',
        'form': form,
        'brigade': brigade,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Brigade/brigade_edit.html', context)


@login_required
def brigade_deactivate_view(request, brigade_id):
    """Деактивация бригады"""

    try:
        # Используем метод из модели
        brigade = Brigade.deactivate_brigade(brigade_id)
        messages.success(
            request,
            f'Бригада "{brigade.name}" успешно деактивирована!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:brigade_list')