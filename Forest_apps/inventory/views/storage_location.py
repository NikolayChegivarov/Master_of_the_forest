from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from Forest_apps.inventory.models import StorageLocation
from Forest_apps.inventory.forms.storage_location import StorageLocationFilterForm


@login_required
def storage_location_list_view(request):
    """Просмотр всех мест хранения"""

    # Получаем все записи
    locations = StorageLocation.objects.all().order_by('source_type', 'id')

    # Фильтрация
    filter_form = StorageLocationFilterForm(request.GET or None)

    if filter_form.is_valid():
        source_type = filter_form.cleaned_data.get('source_type')
        search = filter_form.cleaned_data.get('search')

        if source_type:
            locations = locations.filter(source_type=source_type)

        if search:
            # Фильтруем по названию источника (через get_source_name нельзя, фильтруем по ID)
            # Для поиска по ID или типу
            locations = locations.filter(
                Q(source_id__icontains=search) |
                Q(source_type__icontains=search)
            )

    # Добавляем название источника к каждой записи
    locations_with_names = []
    for location in locations:
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

    # Статистика
    stats = {
        'total': locations.count(),
        'by_type': {
            'склад': locations.filter(source_type='склад').count(),
            'автомобиль': locations.filter(source_type='автомобиль').count(),
            'контрагент': locations.filter(source_type='контрагент').count(),
            'бригады': locations.filter(source_type='бригады').count(),
        }
    }

    context = {
        'title': 'Места хранения',
        'employee_name': request.session.get('employee_name'),
        'locations': locations_with_names,
        'filter_form': filter_form,
        'stats': stats,
    }

    return render(request, 'StorageLocation/storage_location_list.html', context)


@login_required
def storage_location_detail_view(request, location_id):
    """Детальный просмотр места хранения с остатками"""

    from Forest_apps.inventory.models import MaterialBalance

    location = StorageLocation.objects.get(id=location_id)
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
