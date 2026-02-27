from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Forest_apps.core.models import Brigade
from Forest_apps.core.forms.brigade import BrigadeCreateForm, BrigadeEditForm


@login_required
def brigade_list_view(request):
    """Страница со списком бригад (только для должности пользователя)"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    user_position_id = None

    # Находим ID должности по названию
    from Forest_apps.core.models import Position
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        # Если должность не найдена, показываем пустой список
        user_position_id = -1

    # Получаем бригады, созданные этой должностью
    brigades = Brigade.objects.filter(
        created_by_position_id=user_position_id
    ).order_by('-created_at')

    context = {
        'title': 'Бригады',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'brigades': brigades,
    }
    return render(request, 'Brigade/brigade_list.html', context)


@login_required
def brigade_create_view(request):
    """Создание новой бригады"""

    if request.method == 'POST':
        form = BrigadeCreateForm(request.POST)
        if form.is_valid():
            # Сохраняем бригаду
            brigade = form.save(commit=False)

            # Добавляем создателя (пользователя)
            brigade.created_by = request.user

            # Добавляем должность создателя
            from Forest_apps.core.models import Position
            position_name = request.session.get('position_name')
            try:
                position = Position.objects.get(name__iexact=position_name)
                brigade.created_by_position = position
            except Position.DoesNotExist:
                # Если должность не найдена, создаем или используем существующую
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                brigade.created_by_position = position

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
    """Редактирование бригады (только для своей должности)"""

    # Получаем должность текущего пользователя
    from Forest_apps.core.models import Position
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:brigade_list')

    # Получаем бригаду по ID и проверяем, что она создана этой должностью
    brigade = get_object_or_404(
        Brigade,
        id=brigade_id,
        created_by_position=position
    )

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
    """Деактивация бригады (только для своей должности)"""

    # Получаем должность текущего пользователя
    from Forest_apps.core.models import Position
    position_name = request.session.get('position_name')
    try:
        position = Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        messages.error(request, 'Ошибка определения должности')
        return redirect('core:brigade_list')

    try:
        # Проверяем, что бригада создана этой должностью
        brigade = get_object_or_404(
            Brigade,
            id=brigade_id,
            created_by_position=position
        )
        brigade = Brigade.deactivate_brigade(brigade_id)
        messages.success(
            request,
            f'Бригада "{brigade.name}" успешно деактивирована!'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('core:brigade_list')