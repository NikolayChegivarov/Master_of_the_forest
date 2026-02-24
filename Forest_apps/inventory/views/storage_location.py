from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from Forest_apps.inventory.models import StorageLocation, MaterialBalance
from Forest_apps.inventory.forms.storage_location import StorageLocationTypeForm, StorageLocationSearchForm


@login_required
def storage_location_list_view(request):
    """Просмотр всех мест хранения"""

    # Получаем все записи
    locations = StorageLocation.objects.all().order_by('source_type', 'id')

    # Инициализируем формы
    type_form = StorageLocationTypeForm(request.GET or None)
    search_form = StorageLocationSearchForm(request.GET or None)

    # Инициализируем переменные
    source_type = None
    search = None

    # Получаем значения из форм
    if type_form.is_valid():
        source_type = type_form.cleaned_data.get('source_type')

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')

    # Фильтруем по типу в БД
    if source_type:
        locations = locations.filter(source_type=source_type)

    # Получаем все объекты с уже примененным фильтром по типу
    all_locations = list(locations)

    # Если есть поисковый запрос, фильтруем по названиям в памяти
    if search:
        filtered_locations = []
        for location in all_locations:
            try:
                source_name = location.get_source_name().lower()
                if search.lower() in source_name:
                    filtered_locations.append(location)
            except:
                # Если не удалось получить название, проверяем по ID
                if str(location.source_id) == search:
                    filtered_locations.append(location)
        locations_to_show = filtered_locations
    else:
        locations_to_show = all_locations

    # Добавляем название источника к каждой записи
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

    # Статистика (только для отфильтрованных записей)
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
        'title': 'Места хранения',
        'employee_name': request.session.get('employee_name'),
        'locations': locations_with_names,
        'type_form': type_form,
        'search_form': search_form,
        'stats': stats,
    }

    return render(request, 'StorageLocation/storage_location_list.html', context)


@login_required
def storage_location_detail_view(request, location_id):
    """Детальный просмотр места хранения с остатками"""

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

    context = {
        'title': f'Место хранения: {source_name}',
        'employee_name': request.session.get('employee_name'),
        'location': location,
        'source_name': source_name,
        'balances': balances,
        'total_pieces': total_pieces,
        'total_meters': total_meters,
        'total_cubic': total_cubic,
    }

    return render(request, 'StorageLocation/storage_location_detail.html', context)