from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from Forest_apps.forestry.models import CuttingArea, CuttingAreaContent, Material
from Forest_apps.forestry.forms.logging_site_forms import CuttingAreaCreateForm, CuttingAreaEditForm
from Forest_apps.forestry.forms.cutting_area_content_forms import AddMaterialToCuttingAreaForm, \
    UpdateMaterialQuantityForm


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
    """Наполнение лесосеки материалами"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)

    if request.method == 'POST':
        form = AddMaterialToCuttingAreaForm(cutting_area, request.POST)
        if form.is_valid():
            material = form.cleaned_data['material']
            quantity = form.cleaned_data['quantity']

            try:
                # Используем метод модели для добавления/обновления материала
                content, created = cutting_area.update_material_quantity(
                    material.id,
                    quantity
                )

                if created:
                    messages.success(
                        request,
                        f'Материал "{material}" успешно добавлен в лесосеку в количестве {quantity}'
                    )
                else:
                    messages.success(
                        request,
                        f'Количество материала "{material}" обновлено до {quantity}'
                    )

                return redirect('forestry:view_logging_site', cutting_area_id=cutting_area.id)

            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = AddMaterialToCuttingAreaForm(cutting_area)

    # Получаем список материалов для быстрого выбора
    materials = Material.get_all_materials()

    context = {
        'title': f'Наполнение лесосеки: {cutting_area.full_address}',
        'cutting_area': cutting_area,
        'form': form,
        'materials': materials,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/fill_logging_site.html', context)


@login_required
def view_logging_site_view(request, cutting_area_id):
    """Просмотр лесосеки с материалами"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)

    # Получаем все материалы лесосеки
    materials_data = cutting_area.get_all_materials()

    # Получаем общее количество материалов
    total_quantity = cutting_area.get_total_materials_quantity()

    context = {
        'title': f'Просмотр лесосеки: {cutting_area.full_address}',
        'cutting_area': cutting_area,
        'materials': materials_data,
        'total_quantity': total_quantity,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/view_logging_site.html', context)


@login_required
def remove_material_from_cutting_area_view(request, cutting_area_id, material_id):
    """Удаление материала из лесосеки"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)
    material = get_object_or_404(Material, id=material_id)

    try:
        cutting_area.remove_material(material_id)
        messages.success(
            request,
            f'Материал "{material}" успешно удален из лесосеки'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:view_logging_site', cutting_area_id=cutting_area.id)


@login_required
def update_material_quantity_view(request, cutting_area_id, material_id):
    """Обновление количества материала в лесосеке"""

    cutting_area = get_object_or_404(CuttingArea, id=cutting_area_id)
    material = get_object_or_404(Material, id=material_id)

    # Получаем текущее количество
    current_quantity = cutting_area.get_material_quantity(material_id)

    if request.method == 'POST':
        form = UpdateMaterialQuantityForm(request.POST)
        if form.is_valid():
            new_quantity = form.cleaned_data['quantity']

            try:
                cutting_area.update_material_quantity(material_id, new_quantity)
                messages.success(
                    request,
                    f'Количество материала "{material}" обновлено с {current_quantity} до {new_quantity}'
                )
                return redirect('forestry:view_logging_site', cutting_area_id=cutting_area.id)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = UpdateMaterialQuantityForm(initial={'quantity': current_quantity})

    context = {
        'title': f'Обновление количества: {material}',
        'cutting_area': cutting_area,
        'material': material,
        'form': form,
        'current_quantity': current_quantity,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/update_material_quantity.html', context)