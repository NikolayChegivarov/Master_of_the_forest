from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.forestry.models import CuttingArea, CuttingAreaContent
from Forest_apps.forestry.forms.logging_site_forms import CuttingAreaCreateForm, CuttingAreaEditForm


@login_required
def logging_site_view(request):
    """Страница управления лесосеками"""

    # Получаем все активные лесосеки
    active_cutting_areas = CuttingArea.get_active_cutting_areas()

    context = {
        'title': 'Лесосеки',
        'employee_name': request.session.get('employee_name'),
        'cutting_areas': active_cutting_areas,
    }
    return render(request, 'logging_site/logging_site.html', context)


@login_required
def create_logging_site_view(request):
    """Создание новой лесосеки"""

    if request.method == 'POST':
        form = CuttingAreaCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем лесосеку
            cutting_area = form.save()

            # Добавляем сообщение об успехе
            messages.success(
                request,
                f'Лесосека "{cutting_area.full_address}" успешно создана!'
            )

            # Перенаправляем на страницу со списком лесосек
            return redirect('forestry:logging_site')
    else:
        form = CuttingAreaCreateForm()

    context = {
        'title': 'Создание лесосеки',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/create_logging_site.html', context)


@login_required
def edit_logging_site_view(request, cutting_area_id):
    """Редактирование лесосеки"""

    # Получаем лесосеку по ID или возвращаем 404
    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)

    if request.method == 'POST':
        form = CuttingAreaEditForm(request.POST, instance=cutting_area)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Лесосека "{cutting_area.full_address}" успешно обновлена!'
            )
            return redirect('forestry:logging_site')
    else:
        form = CuttingAreaEditForm(instance=cutting_area)

    context = {
        'title': 'Редактирование лесосеки',
        'form': form,
        'cutting_area': cutting_area,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/edit_logging_site.html', context)


@login_required
def deactivate_logging_site_view(request, cutting_area_id):
    """Деактивация лесосеки"""

    try:
        # Используем метод из модели
        cutting_area = CuttingArea.deactivate_cutting_area(cutting_area_id)
        messages.success(
            request,
            f'Лесосека "{cutting_area.full_address}" успешно деактивирована!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:logging_site')


@login_required
def fill_logging_site_view(request, cutting_area_id):
    """Наполнение лесосеки материалами (заглушка)"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)
    messages.info(request, f'Функционал наполнения лесосеки "{cutting_area.full_address}" в разработке')
    return redirect('forestry:logging_site')


@login_required
def view_logging_site_view(request, cutting_area_id):
    """Просмотр лесосеки с материалами (заглушка)"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)
    messages.info(request, f'Функционал просмотра лесосеки "{cutting_area.full_address}" в разработке')
    return redirect('forestry:logging_site')