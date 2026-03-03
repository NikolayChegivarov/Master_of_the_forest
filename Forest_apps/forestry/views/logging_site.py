from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from Forest_apps.forestry.forms.logging_site_forms import CuttingAreaCreateForm, CuttingAreaEditForm
from Forest_apps.forestry.models import CuttingArea, Forestry, Material
from Forest_apps.core.models import Position


@login_required
def logging_site_view(request):
    """Страница со списком лесосек (только для должности пользователя)"""

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

    # Получаем лесосеки, созданные этой должностью
    cutting_areas = CuttingArea.objects.filter(
        created_by_position_id=user_position_id
    ).select_related('forestry', 'created_by_position').order_by('-created_at')

    # Фильтрация по лесничеству (если есть)
    forestry_id = request.GET.get('forestry', '')
    if forestry_id:
        cutting_areas = cutting_areas.filter(forestry_id=forestry_id)

    # Поиск по номеру квартала или выдела
    search_query = request.GET.get('search', '')
    if search_query:
        cutting_areas = cutting_areas.filter(
            Q(quarter_number__icontains=search_query) |
            Q(division_number__icontains=search_query) |
            Q(forestry__name__icontains=search_query)
        )

    # Получаем все лесничества для фильтра
    forestries = Forestry.objects.filter(is_active=True).order_by('name')

    context = {
        'title': 'Лесосеки',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'cutting_areas': cutting_areas,
        'forestries': forestries,
        'current_forestry': forestry_id,
        'search_query': search_query,
    }
    return render(request, 'logging_site/logging_site.html', context)


@login_required
def create_cutting_area_view(request):
    """Создание новой лесосеки"""

    if request.method == 'POST':
        form = CuttingAreaCreateForm(request.POST)  # 👈 ИСПРАВЛЕНО
        if form.is_valid():
            # Сохраняем лесосеку
            cutting_area = form.save(commit=False)

            # Добавляем создателя (пользователя)
            cutting_area.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                cutting_area.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                cutting_area.created_by_position = position

            cutting_area.save()

            messages.success(
                request,
                f'Лесосека {cutting_area.full_address} успешно создана!'
            )

            return redirect('forestry:logging_site')
    else:
        form = CuttingAreaCreateForm()  # 👈 ИСПРАВЛЕНО

    context = {
        'title': 'Создание лесосеки',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/create_logging_site.html', context)


@login_required
def edit_cutting_area_view(request, area_id):
    """Редактирование лесосеки (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:logging_site')

    # Получаем лесосеку по ID и проверяем, что она создана этой должностью
    cutting_area = get_object_or_404(
        CuttingArea,
        id=area_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = CuttingAreaEditForm(request.POST, instance=cutting_area)  # 👈 ИСПРАВЛЕНО
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Лесосека {cutting_area.full_address} успешно обновлена!'
            )
            return redirect('forestry:logging_site')
    else:
        form = CuttingAreaEditForm(instance=cutting_area)  # 👈 ИСПРАВЛЕНО

    context = {
        'title': 'Редактирование лесосеки',
        'form': form,
        'cutting_area': cutting_area,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'logging_site/edit_logging_site.html', context)


@login_required
def deactivate_cutting_area_view(request, area_id):
    """Деактивация лесосеки (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:logging_site')

    try:
        # Проверяем, что лесосека создана этой должностью
        cutting_area = get_object_or_404(
            CuttingArea,
            id=area_id,
            created_by_position=position
        )
        cutting_area = CuttingArea.deactivate_cutting_area(area_id)
        messages.success(
            request,
            f'Лесосека {cutting_area.full_address} успешно деактивирована!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:logging_site')


@login_required
def view_cutting_area_view(request, area_id):
    """Просмотр содержимого лесосеки"""

    # Получаем лесосеку
    cutting_area = get_object_or_404(
        CuttingArea.objects.select_related('forestry', 'created_by_position'),
        id=area_id
    )

    # Получаем все материалы лесосеки
    materials = cutting_area.get_all_materials()

    # Получаем общее количество
    total_quantity = cutting_area.get_total_materials_quantity()

    context = {
        'title': f'Лесосека: {cutting_area.full_address}',
        'employee_name': request.session.get('employee_name'),
        'cutting_area': cutting_area,
        'materials': materials,
        'total_quantity': total_quantity,
    }

    return render(request, 'logging_site/view_logging_site.html', context)


@login_required
def fill_cutting_area_view(request, area_id):
    """Добавление материалов в лесосеку"""

    cutting_area = get_object_or_404(CuttingArea, id=area_id)

    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')

        if material_id and quantity:
            try:
                quantity = float(quantity)
                if quantity <= 0:
                    messages.error(request, 'Количество должно быть больше 0')
                else:
                    result, created = cutting_area.update_material_quantity(material_id, quantity)
                    if created:
                        messages.success(request, 'Материал успешно добавлен в лесосеку!')
                    else:
                        messages.success(request, 'Количество материала успешно обновлено!')
                    return redirect('forestry:view_logging_site', area_id=area_id)
            except ValueError:
                messages.error(request, 'Введите корректное число')
        else:
            messages.error(request, 'Заполните все поля')

    # Получаем все материалы для выпадающего списка
    materials = Material.objects.all().order_by('material_type', 'name')

    context = {
        'title': f'Добавление материала в {cutting_area.full_address}',
        'employee_name': request.session.get('employee_name'),
        'cutting_area': cutting_area,
        'materials': materials,
    }

    return render(request, 'logging_site/fill_logging_site.html', context)


@login_required
def update_material_quantity_view(request, area_id, material_id):
    """Обновление количества конкретного материала в лесосеке"""

    cutting_area = get_object_or_404(CuttingArea, id=area_id)
    material = get_object_or_404(Material, id=material_id)

    # Получаем текущее количество
    current_quantity = cutting_area.get_material_quantity(material_id)

    if request.method == 'POST':
        new_quantity = request.POST.get('quantity')

        if new_quantity:
            try:
                new_quantity = float(new_quantity)
                if new_quantity < 0:
                    messages.error(request, 'Количество не может быть отрицательным')
                elif new_quantity == 0:
                    # Если 0 - удаляем материал
                    cutting_area.remove_material(material_id)
                    messages.success(request, f'Материал "{material.name}" удален из лесосеки')
                    return redirect('forestry:view_logging_site', area_id=area_id)
                else:
                    # Обновляем количество
                    result, created = cutting_area.update_material_quantity(material_id, new_quantity)
                    messages.success(request, f'Количество материала "{material.name}" обновлено')
                    return redirect('forestry:view_logging_site', area_id=area_id)
            except ValueError:
                messages.error(request, 'Введите корректное число')
        else:
            messages.error(request, 'Введите количество')

    context = {
        'title': f'Изменение количества: {material.name}',
        'employee_name': request.session.get('employee_name'),
        'cutting_area': cutting_area,
        'material': material,
        'current_quantity': current_quantity,
    }

    return render(request, 'logging_site/update_material_quantity.html', context)


@login_required
def remove_material_view(request, area_id, material_id):
    """Удаление материала из лесосеки"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:logging_site')

    # Получаем лесосеку и проверяем права
    cutting_area = get_object_or_404(
        CuttingArea,
        id=area_id,
        created_by_position=position
    )

    try:
        cutting_area.remove_material(material_id)
        messages.success(request, 'Материал успешно удален из лесосеки!')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:view_logging_site', area_id=area_id)