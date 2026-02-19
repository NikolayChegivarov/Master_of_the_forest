from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.forestry.models import Forestry
from Forest_apps.forestry.forms.create_forestry import ForestryCreateForm
from Forest_apps.forestry.forms.edit_forestry import ForestryEditForm  # Создадим позже


@login_required
def forestry_view(request):
    """Страница управления лесничествами"""

    # Получаем все активные лесничества
    active_forestries = Forestry.get_active_forestries()

    context = {
        'title': 'Лесничества',
        'employee_name': request.session.get('employee_name'),
        'forestries': active_forestries,
    }
    return render(request, 'forestry/forestry.html', context)


@login_required
def create_forestry_view(request):
    """Создание нового лесничества"""

    if request.method == 'POST':
        form = ForestryCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем лесничество
            forestry = form.save()

            # Добавляем сообщение об успехе
            messages.success(
                request,
                f'Лесничество "{forestry.name}" успешно создано!'
            )

            # Перенаправляем на страницу со списком лесничеств
            return redirect('forestry:forestry')
    else:
        form = ForestryCreateForm()

    context = {
        'title': 'Создание лесничества',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'forestry/create_forestry.html', context)


@login_required
def edit_forestry_view(request, forestry_id):
    """Редактирование лесничества"""

    # Получаем лесничество по ID или возвращаем 404
    forestry = get_object_or_404(Forestry, id=forestry_id)

    if request.method == 'POST':
        form = ForestryEditForm(request.POST, instance=forestry)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Лесничество "{forestry.name}" успешно обновлено!'
            )
            return redirect('forestry:forestry')
    else:
        form = ForestryEditForm(instance=forestry)

    context = {
        'title': 'Редактирование лесничества',
        'form': form,
        'forestry': forestry,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'forestry/edit_forestry.html', context)


@login_required
def deactivate_forestry_view(request, forestry_id):
    """Деактивация лесничества"""

    try:
        # Используем метод из модели
        forestry = Forestry.deactivate_forestry(forestry_id)
        messages.success(
            request,
            f'Лесничество "{forestry.name}" успешно деактивировано!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:forestry')