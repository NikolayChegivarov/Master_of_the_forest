from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Position
from Forest_apps.forestry.forms.material import MaterialCreateForm, MaterialEditForm


@login_required
def materials_view(request):
    """Страница со списком материалов (только для должности пользователя)"""

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

    # Получаем материалы, созданные этой должностью
    materials = Material.objects.filter(
        created_by_position_id=user_position_id
    ).select_related('created_by_position').order_by('material_type', 'name')

    # Фильтрация по типу материала (если есть)
    material_type = request.GET.get('type', '')
    if material_type:
        materials = materials.filter(material_type=material_type)

    # Поиск по названию
    search_query = request.GET.get('search', '')
    if search_query:
        materials = materials.filter(
            Q(name__icontains=search_query) |
            Q(material_type__icontains=search_query)
        )

    # Статистика по типам
    stats_by_type = {
        'древесина': materials.filter(material_type='древесина').count(),
        'ГСМ': materials.filter(material_type='ГСМ').count(),
        'запчасти': materials.filter(material_type='запчасти').count(),
    }

    context = {
        'title': 'Материалы',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'materials': materials,
        'stats_by_type': stats_by_type,
        'current_type': material_type,
        'search_query': search_query,
    }
    return render(request, 'materials/materials.html', context)


@login_required
def material_create_view(request):
    """Создание нового материала"""

    if request.method == 'POST':
        form = MaterialCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем материал
            material = form.save(commit=False)

            # Добавляем создателя (пользователя)
            material.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                material.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                material.created_by_position = position

            material.save()

            messages.success(
                request,
                f'Материал "{material.name}" успешно создан!'
            )

            return redirect('forestry:materials')
    else:
        form = MaterialCreateForm()

    context = {
        'title': 'Создание материала',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'materials/material_create.html', context)


@login_required
def material_edit_view(request, material_id):
    """Редактирование материала (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:materials')

    # Получаем материал по ID и проверяем, что он создан этой должностью
    material = get_object_or_404(
        Material,
        id=material_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = MaterialEditForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Материал "{material.name}" успешно обновлен!'
            )
            return redirect('forestry:materials')
    else:
        form = MaterialEditForm(instance=material)

    context = {
        'title': 'Редактирование материала',
        'form': form,
        'material': material,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'materials/material_edit.html', context)


@login_required
def material_delete_view(request, material_id):
    """Удаление материала (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:materials')

    try:
        # Проверяем, что материал создан этой должностью
        material = get_object_or_404(
            Material,
            id=material_id,
            created_by_position=position
        )
        material.delete()
        messages.success(request, 'Материал успешно удален!')
    except Exception as e:
        messages.error(request, str(e))

    return redirect('forestry:materials')