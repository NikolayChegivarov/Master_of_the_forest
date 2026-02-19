from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.forestry.models import Material
from Forest_apps.forestry.forms.material_forms import MaterialCreateForm, MaterialEditForm


@login_required
def materials_view(request):
    """Страница управления материалами с фильтрацией по типу"""

    # Получаем параметр фильтра из GET-запроса
    material_type = request.GET.get('type', 'all')

    # Базовый запрос
    if material_type == 'all':
        materials = Material.get_all_materials()
    else:
        materials = Material.get_materials_by_type(material_type)

    context = {
        'title': 'Материалы',
        'employee_name': request.session.get('employee_name'),
        'materials': materials,
        'current_filter': material_type,  # Для подсветки выбранного фильтра
    }
    return render(request, 'materials/materials.html', context)


@login_required
def create_material_view(request):
    """Создание нового материала"""

    if request.method == 'POST':
        form = MaterialCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем материал
            material = form.save()

            # Добавляем сообщение об успехе (только одно!)
            messages.success(
                request,
                f'Материал "{material.name}" ({material.get_material_type_display()}) успешно создан!'
            )

            # Перенаправляем на страницу со списком материалов
            return redirect('forestry:materials')
    else:
        form = MaterialCreateForm()

    context = {
        'title': 'Создание материала',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'materials/create_material.html', context)


@login_required
def edit_material_view(request, material_id):
    """Редактирование материала"""

    # Получаем материал по ID или возвращаем 404
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        form = MaterialEditForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Материал "{material.name}" успешно обновлён!'
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

    return render(request, 'materials/edit_material.html', context)


@login_required
def deactivate_material_view(request, material_id):
    """Деактивация материала"""

    try:
        material = get_object_or_404(Material, id=material_id)

        if material.is_active:
            material.is_active = False
            material.save()
            messages.success(
                request,
                f'Материал "{material.name}" успешно деактивирован!'
            )
        else:
            messages.info(
                request,
                f'Материал "{material.name}" уже неактивен'
            )

    except Exception as e:
        messages.error(request, f'Ошибка при деактивации материала: {str(e)}')

    return redirect('forestry:materials')


@login_required
def activate_material_view(request, material_id):
    """Активация материала"""

    try:
        material = get_object_or_404(Material, id=material_id)

        if not material.is_active:
            material.is_active = True
            material.save()
            messages.success(
                request,
                f'Материал "{material.name}" успешно активирован!'
            )
        else:
            messages.info(
                request,
                f'Материал "{material.name}" уже активен'
            )

    except Exception as e:
        messages.error(request, f'Ошибка при активации материала: {str(e)}')

    return redirect('forestry:materials')