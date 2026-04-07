from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from Forest_apps.inventory.models import Conversion
from Forest_apps.core.models import Position
from Forest_apps.inventory.forms.conversion import ConversionCreateForm


@login_required
def conversion_list_view(request):
    """Список конвертаций древесины"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')

    # Получаем склады пользователя через сервис
    from Forest_apps.inventory.services import StorageLocationService
    user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(user_position_name)
    user_warehouse_ids = list(user_warehouses.values_list('id', flat=True))

    # Фильтруем конвертации по складам пользователя
    conversions = Conversion.objects.filter(
        storage_location_id__in=user_warehouse_ids
    ).select_related(
        'storage_location', 'source_material', 'target_material', 'created_by_position'
    ).order_by('-created_at')

    # Статистика
    total_count = conversions.count()
    completed_count = conversions.filter(is_completed=True).count()
    pending_count = conversions.filter(is_completed=False).count()

    context = {
        'title': 'Конвертация древесины',
        'employee_name': request.session.get('employee_name'),
        'position_name': user_position_name,
        'conversions': conversions,
        'total_count': total_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
    }

    return render(request, 'Conversion/conversion_list.html', context)


@login_required
def conversion_create_view(request):
    """Создание новой конвертации древесины"""

    # Получаем должность из сессии
    position_name = request.session.get('position_name')

    if request.method == 'POST':
        form = ConversionCreateForm(request.POST, user=request.user, position_name=position_name)
        if form.is_valid():
            # Сохраняем конвертацию
            conversion = form.save(commit=False)
            conversion.created_by = request.user

            # Добавляем должность создателя
            try:
                position = Position.objects.get(name__iexact=position_name)
                conversion.created_by_position = position
            except Position.DoesNotExist:
                position, _ = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'is_active': True}
                )
                conversion.created_by_position = position

            # Сохраняем
            conversion.save()

            try:
                # Выполняем конвертацию
                conversion.execute_conversion()
                messages.success(
                    request,
                    f'✅ Конвертация №{conversion.id} успешно выполнена! '
                    f'{conversion.source_material.name} → {conversion.target_material.name}'
                )
            except ValueError as e:
                # Если ошибка, удаляем созданную конвертацию
                conversion.delete()
                messages.error(request, str(e))
                return redirect('inventory:conversion_create')

            return redirect('inventory:conversion_list')
    else:
        form = ConversionCreateForm(user=request.user, position_name=position_name)

        # Проверяем, есть ли у пользователя склады
        if form.fields['storage_location'].queryset.count() == 0:
            messages.warning(
                request,
                '⚠️ У вас нет складов для конвертации. Сначала создайте склад.'
            )

    context = {
        'title': 'Создание конвертации',
        'form': form,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Conversion/conversion_create.html', context)


@login_required
def conversion_detail_view(request, conversion_id):
    """Детальный просмотр конвертации"""

    conversion = get_object_or_404(
        Conversion.objects.select_related(
            'storage_location', 'source_material', 'target_material',
            'created_by', 'created_by_position'
        ),
        id=conversion_id
    )

    context = {
        'title': f'Конвертация №{conversion.id}',
        'employee_name': request.session.get('employee_name'),
        'conversion': conversion,
    }

    return render(request, 'Conversion/conversion_detail.html', context)