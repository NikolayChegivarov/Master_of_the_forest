# ПРЕДСТАВЛЕНИЯ КОНВЕРТАЦИИ
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from Forest_apps.inventory.models import Conversion
from Forest_apps.core.models import Position
from Forest_apps.inventory.forms.conversion import ConversionCreateForm


@login_required
def conversion_list_view(request):
    """Список конвертаций древесины"""

    # Получаем должность текущего пользователя из сессии
    user_position_name = request.session.get('position_name')
    is_manager = (user_position_name and user_position_name.lower() == 'руководитель')

    # Вычисляем дату 5 дней назад для проверки возраста
    now_minus_5_days = timezone.now() - timedelta(days=5)

    if is_manager:
        # Руководитель видит ВСЕ конвертации
        conversions = Conversion.objects.select_related(
            'storage_location', 'source_material', 'target_material', 'created_by_position'
        ).order_by('-created_at')
    else:
        # Находим склады, созданные должностью мастера
        from Forest_apps.core.models import Warehouse
        from Forest_apps.inventory.models import StorageLocation

        user_position_id = None
        try:
            position = Position.objects.get(name__iexact=user_position_name)
            user_position_id = position.id
        except Position.DoesNotExist:
            user_position_id = -1

        # Получаем ID складов, принадлежащих должности
        user_warehouse_ids = []
        warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id)
        for wh in warehouses:
            try:
                location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
                user_warehouse_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

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
        'is_manager': is_manager,
        'now_minus_5_days': now_minus_5_days,  # Добавляем для шаблона
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


@login_required
def conversion_edit_view(request, conversion_id):
    """Редактирование конвертации"""

    conversion = get_object_or_404(Conversion, id=conversion_id)
    position_name = request.session.get('position_name')
    is_manager = (position_name and position_name.lower() == 'руководитель')

    # Проверка прав
    if not is_manager:
        # Мастер может редактировать только свои и только младше 5 дней
        from Forest_apps.core.models import Warehouse
        from Forest_apps.inventory.models import StorageLocation

        user_position_id = None
        try:
            position = Position.objects.get(name__iexact=position_name)
            user_position_id = position.id
        except Position.DoesNotExist:
            messages.error(request, 'Ошибка определения должности')
            return redirect('inventory:conversion_list')

        # Получаем склады мастера
        user_warehouse_ids = []
        warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id)
        for wh in warehouses:
            try:
                location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
                user_warehouse_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

        if conversion.storage_location.id not in user_warehouse_ids:
            messages.error(request, 'Вы можете редактировать только свои конвертации')
            return redirect('inventory:conversion_list')

        # ✅ Проверка на возраст (5 дней)
        time_diff = timezone.now() - conversion.created_at
        if time_diff.days >= 5:
            messages.error(request,
                           f'Конвертация старше 5 дней (создана {conversion.created_at.date()}), редактирование невозможно. Обратитесь к руководителю.')
            return redirect('inventory:conversion_list')

    if request.method == 'POST':
        form = ConversionCreateForm(request.POST, instance=conversion, user=request.user, position_name=position_name)
        if form.is_valid():
            # Сохраняем конвертацию
            updated_conversion = form.save(commit=False)

            # Проверяем, была ли конвертация уже выполнена
            was_completed = conversion.is_completed

            # Откатываем старые остатки, если конвертация была выполнена
            if was_completed:
                from Forest_apps.inventory.models import MaterialBalance
                try:
                    # Отменяем старую конвертацию
                    from Forest_apps.inventory.models import MaterialBalance

                    # Получаем баланс исходного материала
                    source_balance = MaterialBalance.objects.get(
                        storage_location=conversion.storage_location,
                        material=conversion.source_material
                    )
                    # Возвращаем списанное количество
                    if conversion.source_quantity_pieces:
                        source_balance.quantity_pieces += conversion.source_quantity_pieces
                    if conversion.source_quantity_meters:
                        source_balance.quantity_meters = (
                                                                     source_balance.quantity_meters or 0) + conversion.source_quantity_meters
                    if conversion.source_quantity_cubic:
                        source_balance.quantity_cubic = (
                                                                    source_balance.quantity_cubic or 0) + conversion.source_quantity_cubic
                    source_balance.save()

                    # Получаем баланс целевого материала
                    try:
                        target_balance = MaterialBalance.objects.get(
                            storage_location=conversion.storage_location,
                            material=conversion.target_material
                        )
                        # Убираем созданное количество
                        if conversion.target_quantity_pieces:
                            target_balance.quantity_pieces -= conversion.target_quantity_pieces
                        if conversion.target_quantity_meters:
                            target_balance.quantity_meters = (
                                                                         target_balance.quantity_meters or 0) - conversion.target_quantity_meters
                        if conversion.target_quantity_cubic:
                            target_balance.quantity_cubic = (
                                                                        target_balance.quantity_cubic or 0) - conversion.target_quantity_cubic
                        target_balance.save()
                    except MaterialBalance.DoesNotExist:
                        pass

                except MaterialBalance.DoesNotExist:
                    pass

            # Сохраняем обновленную конвертацию
            updated_conversion.is_completed = False
            updated_conversion.completed_at = None
            updated_conversion.save()

            # Выполняем конвертацию заново
            try:
                updated_conversion.execute_conversion()
                messages.success(request, f'✅ Конвертация №{updated_conversion.id} успешно обновлена и выполнена!')
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('inventory:conversion_edit', conversion_id=conversion.id)

            return redirect('inventory:conversion_list')
    else:
        form = ConversionCreateForm(instance=conversion, user=request.user, position_name=position_name)

    context = {
        'title': f'Редактирование конвертации №{conversion.id}',
        'form': form,
        'conversion': conversion,
        'employee_name': request.session.get('employee_name'),
    }

    return render(request, 'Conversion/conversion_create.html', context)


@login_required
def conversion_delete_view(request, conversion_id):
    """Удаление конвертации"""

    conversion = get_object_or_404(Conversion, id=conversion_id)
    position_name = request.session.get('position_name')
    is_manager = (position_name and position_name.lower() == 'руководитель')

    # Проверка прав
    if not is_manager:
        from Forest_apps.core.models import Warehouse
        from Forest_apps.inventory.models import StorageLocation

        user_position_id = None
        try:
            position = Position.objects.get(name__iexact=position_name)
            user_position_id = position.id
        except Position.DoesNotExist:
            messages.error(request, 'Ошибка определения должности')
            return redirect('inventory:conversion_list')

        # Получаем склады мастера
        user_warehouse_ids = []
        warehouses = Warehouse.objects.filter(created_by_position_id=user_position_id)
        for wh in warehouses:
            try:
                location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
                user_warehouse_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

        if conversion.storage_location.id not in user_warehouse_ids:
            messages.error(request, 'Вы можете удалять только свои конвертации')
            return redirect('inventory:conversion_list')

        # ✅ Проверка на возраст (5 дней)
        time_diff = timezone.now() - conversion.created_at
        if time_diff.days >= 5:
            messages.error(request,
                           f'Конвертация старше 5 дней (создана {conversion.created_at.date()}), удаление невозможно. Обратитесь к руководителю.')
            return redirect('inventory:conversion_list')

    try:
        # Откатываем остатки, если конвертация выполнена
        if conversion.is_completed:
            from Forest_apps.inventory.models import MaterialBalance

            # Возвращаем списанный исходный материал
            try:
                source_balance = MaterialBalance.objects.get(
                    storage_location=conversion.storage_location,
                    material=conversion.source_material
                )
                if conversion.source_quantity_pieces:
                    source_balance.quantity_pieces += conversion.source_quantity_pieces
                if conversion.source_quantity_meters:
                    source_balance.quantity_meters = (
                                                                 source_balance.quantity_meters or 0) + conversion.source_quantity_meters
                if conversion.source_quantity_cubic:
                    source_balance.quantity_cubic = (
                                                                source_balance.quantity_cubic or 0) + conversion.source_quantity_cubic
                source_balance.save()
            except MaterialBalance.DoesNotExist:
                pass

            # Убираем созданный целевой материал
            try:
                target_balance = MaterialBalance.objects.get(
                    storage_location=conversion.storage_location,
                    material=conversion.target_material
                )
                if conversion.target_quantity_pieces:
                    target_balance.quantity_pieces -= conversion.target_quantity_pieces
                if conversion.target_quantity_meters:
                    target_balance.quantity_meters = (
                                                                 target_balance.quantity_meters or 0) - conversion.target_quantity_meters
                if conversion.target_quantity_cubic:
                    target_balance.quantity_cubic = (
                                                                target_balance.quantity_cubic or 0) - conversion.target_quantity_cubic
                target_balance.save()
            except MaterialBalance.DoesNotExist:
                pass

            messages.info(request, f'Остатки материалов восстановлены для конвертации №{conversion.id}')

        conversion_id_for_message = conversion.id
        conversion.delete()
        messages.success(request, f'✅ Конвертация №{conversion_id_for_message} успешно удалена!')

    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory:conversion_list')