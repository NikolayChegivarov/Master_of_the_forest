from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.forestry.models import Forestry
from Forest_apps.core.models import Position
from Forest_apps.forestry.forms.create_forestry import ForestryCreateForm  # 👈 ИСПРАВЛЕНО
from Forest_apps.forestry.forms.edit_forestry import ForestryEditForm  # 👈 ИСПРАВЛЕНО


@login_required
def forestry_view(request):
    """Страница управления лесничествами (только для должности пользователя)"""

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

    # Получаем лесничества, созданные этой должностью
    forestries = Forestry.objects.filter(
        created_by_position_id=user_position_id
    ).order_by('-created_at')

    context = {
        'title': 'Лесничества',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'forestries': forestries,
    }
    return render(request, 'forestry/forestry.html', context)


@login_required
def create_forestry_view(request):
    """Создание нового лесничества"""

    if request.method == 'POST':
        form = ForestryCreateForm(request.POST)  # 👈 ИСПРАВЛЕНО
        if form.is_valid():
            # Сохраняем лесничество
            forestry = form.save(commit=False)

            # Добавляем создателя (пользователя)
            forestry.created_by = request.user

            # Добавляем должность создателя
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                forestry.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                forestry.created_by_position = position

            forestry.save()

            messages.success(
                request,
                f'Лесничество "{forestry.name}" успешно создано!'
            )

            return redirect('forestry:forestry')
    else:
        form = ForestryCreateForm()  # 👈 ИСПРАВЛЕНО

    context = {
        'title': 'Создание лесничества',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'forestry/create_forestry.html', context)


@login_required
def edit_forestry_view(request, forestry_id):
    """Редактирование лесничества (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:forestry')

    # Получаем лесничество по ID и проверяем, что оно создано этой должностью
    forestry = get_object_or_404(
        Forestry,
        id=forestry_id,
        created_by_position=position
    )

    if request.method == 'POST':
        form = ForestryEditForm(request.POST, instance=forestry)  # 👈 ИСПРАВЛЕНО
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Лесничество "{forestry.name}" успешно обновлено!'
            )
            return redirect('forestry:forestry')
    else:
        form = ForestryEditForm(instance=forestry)  # 👈 ИСПРАВЛЕНО

    context = {
        'title': 'Редактирование лесничества',
        'form': form,
        'forestry': forestry,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'forestry/edit_forestry.html', context)


@login_required
def deactivate_forestry_view(request, forestry_id):
    """Деактивация лесничества (только для своей должности)"""

    # Получаем должность текущего пользователя
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('forestry:forestry')

    try:
        # Проверяем, что лесничество создано этой должностью
        forestry = get_object_or_404(
            Forestry,
            id=forestry_id,
            created_by_position=position
        )
        forestry = Forestry.deactivate_forestry(forestry_id)
        messages.success(
            request,
            f'Лесничество "{forestry.name}" успешно деактивировано!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('forestry:forestry')