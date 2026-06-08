# ПРЕДСТАВЛЕНИЯ КОНВЕРТАЦИИ
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from Forest_apps.inventory.models import Conversion, MaterialBalance
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

            # Сохраняем (дата уже установлена в форме)
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
    """Редактирование конвертации: откат старой + применение новой"""

    conversion = get_object_or_404(Conversion, id=conversion_id)
    position_name = request.session.get('position_name')
    is_manager = (position_name and position_name.lower() == 'руководитель')

    # Проверка прав (оставляем как есть)
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

        time_diff = timezone.now() - conversion.created_at
        if time_diff.days >= 5:
            messages.error(request, f'Конвертация старше 5 дней, редактирование невозможно')
            return redirect('inventory:conversion_list')

    if request.method == 'POST':
        # ===== 1. СОХРАНЯЕМ СТАРЫЕ ДАННЫЕ ДО ИЗМЕНЕНИЯ ФОРМЫ =====
        storage_location = conversion.storage_location

        old_source = conversion.source_material
        old_source_pieces = conversion.source_quantity_pieces or 0
        old_source_meters = conversion.source_quantity_meters or 0
        old_source_cubic = conversion.source_quantity_cubic or 0

        old_target = conversion.target_material
        old_target_pieces = conversion.target_quantity_pieces or 0
        old_target_meters = conversion.target_quantity_meters or 0
        old_target_cubic = conversion.target_quantity_cubic or 0

        print("\n" + "=" * 80)
        print(f"РЕДАКТИРОВАНИЕ КОНВЕРТАЦИИ #{conversion.id}")
        print("=" * 80)

        print("\n📊 ПЕРВОНАЧАЛЬНЫЕ ОСТАТКИ В БАЗЕ ДАННЫХ:")
        print("-" * 50)

        # Получаем остатки ДО начала любых изменений
        try:
            old_source_balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=old_source
            )
            old_source_qty = old_source_balance.quantity_pieces
            print(f"{old_source.name}: {old_source_qty} шт")
        except MaterialBalance.DoesNotExist:
            old_source_balance = None
            old_source_qty = 0
            print(f"{old_source.name}: 0 шт")

        try:
            old_target_balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=old_target
            )
            old_target_qty = old_target_balance.quantity_pieces
            print(f"{old_target.name}: {old_target_qty} шт")
        except MaterialBalance.DoesNotExist:
            old_target_balance = None
            old_target_qty = 0
            print(f"{old_target.name}: 0 шт")

        print(f"\n📋 СТАРАЯ КОНВЕРТАЦИЯ (из базы данных):")
        print(f"   -{old_source_pieces} {old_source.name} → +{old_target_pieces} {old_target.name}")

        # ===== 2. ТЕПЕРЬ СОЗДАЁМ ФОРМУ И ПОЛУЧАЕМ НОВЫЕ ДАННЫЕ =====
        form = ConversionCreateForm(request.POST, instance=conversion, user=request.user, position_name=position_name)

        if form.is_valid():
            try:
                # ===== 3. НОВАЯ КОНВЕРТАЦИЯ ИЗ ФОРМЫ =====
                new_source = form.cleaned_data.get('source_material')
                new_source_pieces = form.cleaned_data.get('source_quantity_pieces') or 0
                new_source_meters = form.cleaned_data.get('source_quantity_meters') or 0
                new_source_cubic = form.cleaned_data.get('source_quantity_cubic') or 0

                new_target = form.cleaned_data.get('target_material')
                new_target_pieces = form.cleaned_data.get('target_quantity_pieces') or 0
                new_target_meters = form.cleaned_data.get('target_quantity_meters') or 0
                new_target_cubic = form.cleaned_data.get('target_quantity_cubic') or 0

                print(f"\n📋 НОВАЯ КОНВЕРТАЦИЯ (из формы):")
                print(f"   -{new_source_pieces} {new_source.name} → +{new_target_pieces} {new_target.name}")

                # ===== 4. ОТКАТ СТАРОЙ КОНВЕРТАЦИИ =====
                print("\n" + "=" * 80)
                print("ШАГ 1: ОТКАТ СТАРОЙ КОНВЕРТАЦИИ")
                print("=" * 80)

                # Возвращаем исходный материал
                print(f"\n1️⃣ Возвращаем списанный исходный материал: +{old_source_pieces} {old_source.name}")
                if old_source_balance:
                    before = old_source_balance.quantity_pieces
                    old_source_balance.quantity_pieces += old_source_pieces
                    old_source_balance.quantity_meters = (old_source_balance.quantity_meters or 0) + old_source_meters
                    old_source_balance.quantity_cubic = (old_source_balance.quantity_cubic or 0) + old_source_cubic
                    old_source_balance.save()
                    print(
                        f"   {old_source.name}: {before} → {old_source_balance.quantity_pieces} шт (+{old_source_pieces})")
                else:
                    old_source_balance = MaterialBalance.objects.create(
                        storage_location=storage_location,
                        material=old_source,
                        quantity_pieces=old_source_pieces,
                        quantity_meters=old_source_meters,
                        quantity_cubic=old_source_cubic
                    )
                    print(f"   Создан новый баланс: {old_source.name}: {old_source_pieces} шт")

                # Удаляем целевой материал
                print(f"\n2️⃣ Удаляем созданный целевой материал: -{old_target_pieces} {old_target.name}")
                if old_target_balance:
                    if old_target_balance.quantity_pieces < old_target_pieces:
                        raise ValueError(
                            f'Невозможно откатить конвертацию: "{old_target.name}" недостаточно на складе. В наличии: {old_target_balance.quantity_pieces}, требуется удалить: {old_target_pieces}')

                    before = old_target_balance.quantity_pieces
                    old_target_balance.quantity_pieces -= old_target_pieces
                    old_target_balance.quantity_meters = (old_target_balance.quantity_meters or 0) - old_target_meters
                    old_target_balance.quantity_cubic = (old_target_balance.quantity_cubic or 0) - old_target_cubic
                    old_target_balance.save()
                    print(
                        f"   {old_target.name}: {before} → {old_target_balance.quantity_pieces} шт (-{old_target_pieces})")
                else:
                    if old_target_pieces > 0:
                        raise ValueError(f'Невозможно откатить конвертацию: "{old_target.name}" отсутствует на складе')
                    print(f"   Целевой материал отсутствовал, пропускаем")

                # Показываем остатки после отката
                print("\n📊 ОСТАТКИ ПОСЛЕ ОТКАТА:")
                after_source = MaterialBalance.objects.filter(
                    storage_location=storage_location,
                    material=old_source
                ).first()
                after_target = MaterialBalance.objects.filter(
                    storage_location=storage_location,
                    material=old_target
                ).first()
                print(f"{old_source.name}: {after_source.quantity_pieces if after_source else 0} шт")
                print(f"{old_target.name}: {after_target.quantity_pieces if after_target else 0} шт")

                # ===== 5. ПРИМЕНЕНИЕ НОВОЙ КОНВЕРТАЦИИ =====
                print("\n" + "=" * 80)
                print("ШАГ 2: ПРИМЕНЕНИЕ НОВОЙ КОНВЕРТАЦИИ")
                print("=" * 80)
                print(
                    f"Новая конвертация: -{new_source_pieces} {new_source.name} → +{new_target_pieces} {new_target.name}")

                # Получаем актуальные балансы для новых материалов
                try:
                    new_source_balance = MaterialBalance.objects.get(
                        storage_location=storage_location,
                        material=new_source
                    )
                except MaterialBalance.DoesNotExist:
                    new_source_balance = None

                # Списываем исходный материал
                print(f"\n1️⃣ Списываем исходный материал: -{new_source_pieces} {new_source.name}")
                if new_source_balance:
                    if new_source_balance.quantity_pieces < new_source_pieces:
                        raise ValueError(
                            f'Недостаточно "{new_source.name}" на складе. В наличии: {new_source_balance.quantity_pieces}, требуется: {new_source_pieces}')

                    before = new_source_balance.quantity_pieces
                    new_source_balance.quantity_pieces -= new_source_pieces
                    new_source_balance.quantity_meters = (new_source_balance.quantity_meters or 0) - new_source_meters
                    new_source_balance.quantity_cubic = (new_source_balance.quantity_cubic or 0) - new_source_cubic
                    new_source_balance.save()
                    print(
                        f"   {new_source.name}: {before} → {new_source_balance.quantity_pieces} шт (-{new_source_pieces})")
                else:
                    if new_source_pieces > 0:
                        raise ValueError(f'Материал "{new_source.name}" отсутствует на складе')
                    print(f"   Исходный материал отсутствует, пропускаем")

                # Создаём целевой материал
                print(f"\n2️⃣ Создаём целевой материал: +{new_target_pieces} {new_target.name}")
                try:
                    new_target_balance = MaterialBalance.objects.get(
                        storage_location=storage_location,
                        material=new_target
                    )
                    before = new_target_balance.quantity_pieces
                    new_target_balance.quantity_pieces += new_target_pieces
                    new_target_balance.quantity_meters = (new_target_balance.quantity_meters or 0) + new_target_meters
                    new_target_balance.quantity_cubic = (new_target_balance.quantity_cubic or 0) + new_target_cubic
                    new_target_balance.save()
                    print(
                        f"   {new_target.name}: {before} → {new_target_balance.quantity_pieces} шт (+{new_target_pieces})")
                except MaterialBalance.DoesNotExist:
                    MaterialBalance.objects.create(
                        storage_location=storage_location,
                        material=new_target,
                        quantity_pieces=new_target_pieces,
                        quantity_meters=new_target_meters,
                        quantity_cubic=new_target_cubic,
                        created_by=request.user,
                        created_by_position=conversion.created_by_position
                    )
                    print(f"   Создан новый баланс: {new_target.name}: {new_target_pieces} шт")

                # ===== 6. ФИНАЛЬНЫЕ ОСТАТКИ =====
                print("\n" + "=" * 80)
                print("📊 ОСТАТКИ ПОСЛЕ РЕДАКТИРОВАНИЯ:")
                print("-" * 50)

                final_source = MaterialBalance.objects.filter(
                    storage_location=storage_location,
                    material=new_source
                ).first()
                final_target = MaterialBalance.objects.filter(
                    storage_location=storage_location,
                    material=new_target
                ).first()

                print(f"{new_source.name}: {final_source.quantity_pieces if final_source else 0} шт")
                print(f"{new_target.name}: {final_target.quantity_pieces if final_target else 0} шт")

                # ===== 7. ОБНОВЛЯЕМ ЗАПИСЬ КОНВЕРТАЦИИ =====
                conversion.source_material = new_source
                conversion.source_quantity_pieces = new_source_pieces
                conversion.source_quantity_meters = new_source_meters
                conversion.source_quantity_cubic = new_source_cubic
                conversion.target_material = new_target
                conversion.target_quantity_pieces = new_target_pieces
                conversion.target_quantity_meters = new_target_meters
                conversion.target_quantity_cubic = new_target_cubic
                conversion.conversion_date = form.cleaned_data.get('conversion_date', timezone.now())
                conversion.save()

                print("\n" + "=" * 80)
                print(f"✅ КОНВЕРТАЦИЯ #{conversion.id} УСПЕШНО ОБНОВЛЕНА")
                print("=" * 80 + "\n")

                messages.success(request, f'✅ Конвертация №{conversion.id} успешно обновлена!')
                return redirect('inventory:conversion_list')

            except ValueError as e:
                print(f"\n❌ ОШИБКА: {str(e)}")
                messages.error(request, str(e))
                return redirect('inventory:conversion_edit', conversion_id=conversion.id)
            except Exception as e:
                print(f"\n❌ ОШИБКА: {str(e)}")
                messages.error(request, f'Ошибка: {str(e)}')
                return redirect('inventory:conversion_edit', conversion_id=conversion.id)
        else:
            context = {
                'title': f'Редактирование конвертации №{conversion.id}',
                'form': form,
                'conversion': conversion,
                'employee_name': request.session.get('employee_name'),
            }
            return render(request, 'Conversion/conversion_create.html', context)
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
    """Удаление конвертации с откатом остатков"""

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

        time_diff = timezone.now() - conversion.created_at
        if time_diff.days >= 5:
            messages.error(request,
                           f'Конвертация старше 5 дней (создана {conversion.created_at.date()}), удаление невозможно. Обратитесь к руководителю.')
            return redirect('inventory:conversion_list')

    try:
        from Forest_apps.inventory.models import MaterialBalance

        storage_location = conversion.storage_location

        # Возвращаем исходный материал
        try:
            source_balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=conversion.source_material
            )
            source_balance.quantity_pieces += conversion.source_quantity_pieces or 0
            source_balance.quantity_meters = (source_balance.quantity_meters or 0) + (
                        conversion.source_quantity_meters or 0)
            source_balance.quantity_cubic = (source_balance.quantity_cubic or 0) + (
                        conversion.source_quantity_cubic or 0)
            source_balance.save()
        except MaterialBalance.DoesNotExist:
            pass

        # Убираем созданный материал
        try:
            target_balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=conversion.target_material
            )
            target_balance.quantity_pieces -= conversion.target_quantity_pieces or 0
            target_balance.quantity_meters = (target_balance.quantity_meters or 0) - (
                        conversion.target_quantity_meters or 0)
            target_balance.quantity_cubic = (target_balance.quantity_cubic or 0) - (
                        conversion.target_quantity_cubic or 0)
            target_balance.save()
        except MaterialBalance.DoesNotExist:
            pass

        conversion_id_for_message = conversion.id
        conversion.delete()
        messages.success(request, f'✅ Конвертация №{conversion_id_for_message} успешно удалена!')

    except Exception as e:
        messages.error(request, str(e))

    return redirect('inventory:conversion_list')