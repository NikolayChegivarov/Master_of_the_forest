# ПРЕДСТАВЛЕНИЯ МЕСТ ХРАНЕНИЯ
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from Forest_apps.inventory.models import StorageLocation, MaterialBalance
from Forest_apps.inventory.forms.storage_location import StorageLocationTypeForm, StorageLocationSearchForm
from Forest_apps.inventory.services import StorageLocationService
from Forest_apps.core.models import Position


@login_required
def storage_location_list_view(request):
    """Просмотр ВСЕХ мест хранения (административная функция)"""

    # Получаем все записи
    locations = StorageLocation.objects.all().order_by('source_type', 'id')

    # Инициализируем формы
    type_form = StorageLocationTypeForm(request.GET or None)
    search_form = StorageLocationSearchForm(request.GET or None)

    source_type = None
    search = None

    if type_form.is_valid():
        source_type = type_form.cleaned_data.get('source_type')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')

    if source_type:
        locations = locations.filter(source_type=source_type)

    all_locations = list(locations)

    if search:
        filtered_locations = []
        for location in all_locations:
            try:
                source_name = location.get_source_name().lower()
                if search.lower() in source_name:
                    filtered_locations.append(location)
            except:
                if str(location.source_id) == search:
                    filtered_locations.append(location)
        locations_to_show = filtered_locations
    else:
        locations_to_show = all_locations

    locations_with_names = []
    for location in locations_to_show:
        try:
            source_name = location.get_source_name()
        except:
            source_name = "Ошибка получения названия"

        locations_with_names.append({
            'id': location.id,
            'source_type': location.get_source_type_display(),
            'source_type_raw': location.source_type,
            'source_id': location.source_id,
            'source_name': source_name,
            'obj': location
        })

    stats = {
        'total': len(locations_to_show),
        'by_type': {
            'склад': sum(1 for l in locations_to_show if l.source_type == 'склад'),
            'автомобиль': sum(1 for l in locations_to_show if l.source_type == 'автомобиль'),
            'контрагент': sum(1 for l in locations_to_show if l.source_type == 'контрагент'),
            'бригады': sum(1 for l in locations_to_show if l.source_type == 'бригады'),
        }
    }

    context = {
        'title': 'Все места хранения',
        'employee_name': request.session.get('employee_name'),
        'locations': locations_with_names,
        'type_form': type_form,
        'search_form': search_form,
        'stats': stats,
    }

    return render(request, 'StorageLocation/storage_location_list.html', context)


@login_required
def my_storage_location_list_view(request):
    """Просмотр мест хранения ТОЛЬКО для должности пользователя"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')

    # Получаем места хранения через сервис
    user_locations = StorageLocationService.get_user_storage_locations_by_position_name(
        user_position_name
    )

    # Получаем ID должности для отображения в заголовке
    user_position_id = None
    try:
        position = Position.objects.get(name__iexact=user_position_name)
        user_position_id = position.id
    except Position.DoesNotExist:
        user_position_id = -1

    # Инициализируем формы
    type_form = StorageLocationTypeForm(request.GET or None)
    search_form = StorageLocationSearchForm(request.GET or None)

    source_type = None
    search = None

    if type_form.is_valid():
        source_type = type_form.cleaned_data.get('source_type')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')

    # Фильтруем по типу
    if source_type:
        user_locations = user_locations.filter(source_type=source_type)

    all_locations = list(user_locations)

    # Поиск по названию
    if search:
        filtered_locations = []
        for location in all_locations:
            try:
                source_name = location.get_source_name().lower()
                if search.lower() in source_name:
                    filtered_locations.append(location)
            except:
                if str(location.source_id) == search:
                    filtered_locations.append(location)
        locations_to_show = filtered_locations
    else:
        locations_to_show = all_locations

    locations_with_names = []
    for location in locations_to_show:
        try:
            source_name = location.get_source_name()
        except:
            source_name = "Ошибка получения названия"

        locations_with_names.append({
            'id': location.id,
            'source_type': location.get_source_type_display(),
            'source_type_raw': location.source_type,
            'source_id': location.source_id,
            'source_name': source_name,
            'obj': location
        })

    stats = {
        'total': len(locations_to_show),
        'by_type': {
            'склад': sum(1 for l in locations_to_show if l.source_type == 'склад'),
            'автомобиль': sum(1 for l in locations_to_show if l.source_type == 'автомобиль'),
            'контрагент': sum(1 for l in locations_to_show if l.source_type == 'контрагент'),
            'бригады': sum(1 for l in locations_to_show if l.source_type == 'бригады'),
        }
    }

    context = {
        'title': 'Мои места хранения',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'locations': locations_with_names,
        'type_form': type_form,
        'search_form': search_form,
        'stats': stats,
    }

    return render(request, 'StorageLocation/my_storage_location_list.html', context)


@login_required
def storage_location_detail_view(request, location_id):
    """Детальный просмотр места хранения (общий)"""

    location = get_object_or_404(StorageLocation, id=location_id)
    source_name = location.get_source_name()

    # Получаем остатки для этого места хранения
    balances = MaterialBalance.objects.filter(
        storage_location=location
    ).select_related('material').order_by('material__material_type', 'material__name')

    # Подсчет итогов
    total_pieces = sum(b.quantity_pieces for b in balances)
    total_meters = sum(b.quantity_meters or 0 for b in balances)
    total_cubic = sum(b.quantity_cubic or 0 for b in balances)

    # Передаем параметр для кнопки "назад"
    context = {
        'title': f'Место хранения: {source_name}',
        'employee_name': request.session.get('employee_name'),
        'location': location,
        'source_name': source_name,
        'balances': balances,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
        'back_url': 'inventory:storage_location_list',  # Куда возвращаться
        'back_text': '← К списку всех мест',
    }

    return render(request, 'StorageLocation/storage_location_detail.html', context)


@login_required
def my_storage_location_detail_view(request, location_id):
    """Детальный просмотр места хранения (только для моих мест)"""

    location = get_object_or_404(StorageLocation, id=location_id)
    source_name = location.get_source_name()

    # Проверяем, принадлежит ли место хранения должности пользователя
    user_position_name = request.session.get('position_name')
    user_locations = StorageLocationService.get_user_storage_locations_by_position_name(
        user_position_name
    )
    user_location_ids = list(user_locations.values_list('id', flat=True))

    if location.id not in user_location_ids:
        # Если место не принадлежит пользователю, показываем сообщение
        context = {
            'title': 'Доступ запрещен',
            'employee_name': request.session.get('employee_name'),
            'error_message': 'У вас нет доступа к этому месту хранения',
        }
        return render(request, 'StorageLocation/storage_location_detail.html', context)

    # Получаем остатки для этого места хранения
    balances = MaterialBalance.objects.filter(
        storage_location=location
    ).select_related('material').order_by('material__material_type', 'material__name')

    # Подсчет итогов
    total_pieces = sum(b.quantity_pieces for b in balances)
    total_meters = sum(b.quantity_meters or 0 for b in balances)
    total_cubic = sum(b.quantity_cubic or 0 for b in balances)

    # Передаем параметр для кнопки "назад"
    context = {
        'title': f'Мое место хранения: {source_name}',
        'employee_name': request.session.get('employee_name'),
        'location': location,
        'source_name': source_name,
        'balances': balances,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
        'back_url': 'inventory:my_storage_location_list',  # Куда возвращаться
        'back_text': '← К списку моих мест',
    }

    return render(request, 'StorageLocation/storage_location_detail.html', context)