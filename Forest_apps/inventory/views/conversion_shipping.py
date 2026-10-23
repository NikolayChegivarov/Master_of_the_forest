# Forest_apps/inventory/views/conversion_shipping.py
"""
Представления для массовой отправки целевого материала из конвертаций.

Пользователь выбирает несколько конвертаций на странице /inventory/conversions/,
нажимает "Отправить целевой материал", и система формирует документ движения
с общими полями (тип движения, откуда, куда, водитель, ТС, № вагона)
и таблицей материалов из целевых материалов выбранных конвертаций.

Дубликаты (одинаковый целевой материал из нескольких конвертаций) складываются.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from Forest_apps.inventory.models import (
    Conversion,
    MaterialMovement,
    StorageLocation,
    MaterialBalance,
)
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Position, Warehouse, Brigade, Vehicle
from Forest_apps.employees.models import Employee
from Forest_apps.inventory.services import StorageLocationService


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _get_user_position_name(request):
    """Возвращает название должности пользователя из сессии."""
    return request.session.get('position_name')


def _get_user_position(request):
    """Возвращает объект Position текущего пользователя или None."""
    position_name = _get_user_position_name(request)
    if not position_name:
        return None
    try:
        return Position.objects.get(name__iexact=position_name)
    except Position.DoesNotExist:
        return None


def _get_user_location_ids(position):
    """Возвращает список ID мест хранения, принадлежащих должности."""
    if not position:
        return []

    location_ids = []

    warehouses = Warehouse.objects.filter(created_by_position=position)
    for wh in warehouses:
        try:
            loc = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
            location_ids.append(loc.id)
        except StorageLocation.DoesNotExist:
            pass

    brigades = Brigade.objects.filter(created_by_position=position)
    for br in brigades:
        try:
            loc = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
            location_ids.append(loc.id)
        except StorageLocation.DoesNotExist:
            pass

    vehicles = Vehicle.objects.filter(created_by_position=position)
    for vh in vehicles:
        try:
            loc = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
            location_ids.append(loc.id)
        except StorageLocation.DoesNotExist:
            pass

    return location_ids


def _get_user_warehouses(position):
    """Возвращает QuerySet складов, принадлежащих должности."""
    if not position:
        return StorageLocation.objects.none()
    return StorageLocationService.get_user_warehouses_by_position_name(position.name)


def _parse_conversion_ids(raw_value):
    """
    Разбирает строку '1,2,3' в список ID.
    Возвращает список int или пустой список.
    """
    if not raw_value:
        return []
    result = []
    for part in raw_value.split(','):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


def _aggregate_target_materials(conversions):
    """
    Объединяет целевые материалы из конвертаций.

    Возвращает список словарей:
        [
            {
                'material': Material,
                'material_id': int,
                'quantity_pieces': Decimal,
                'quantity_meters': Decimal,
                'quantity_cubic': Decimal,
                'conversion_ids': [1, 2, 3],   # из каких конвертаций пришло
            },
            ...
        ]

    Дубликаты по material_id складываются.
    """
    aggregated = {}

    for conversion in conversions:
        material = conversion.target_material
        key = material.id

        if key not in aggregated:
            aggregated[key] = {
                'material': material,
                'material_id': material.id,
                'quantity_pieces': Decimal('0'),
                'quantity_meters': Decimal('0'),
                'quantity_cubic': Decimal('0'),
                'conversion_ids': [],
            }

        entry = aggregated[key]
        entry['quantity_pieces'] += conversion.target_quantity_pieces or Decimal('0')
        entry['quantity_meters'] += conversion.target_quantity_meters or Decimal('0')
        entry['quantity_cubic'] += conversion.target_quantity_cubic or Decimal('0')
        entry['conversion_ids'].append(conversion.id)

    # Сортируем по названию материала для предсказуемого порядка
    result = list(aggregated.values())
    result.sort(key=lambda x: x['material'].name.lower())
    return result


def _get_available_locations_for_type(position, accounting_type):
    """
    Возвращает (from_locations, to_locations) — QuerySet'ы мест хранения
    в зависимости от типа движения (аналогично API get_locations_by_type).
    """
    user_location_ids = _get_user_location_ids(position)

    if accounting_type == 'Перемещение':
        from_qs = StorageLocation.objects.filter(id__in=user_location_ids)
        to_qs = StorageLocation.objects.filter(id__in=user_location_ids)

    elif accounting_type == 'Отправление':
        from_qs = StorageLocation.objects.filter(id__in=user_location_ids)
        to_qs = StorageLocation.objects.exclude(
            id__in=user_location_ids
        ).exclude(source_type='контрагент')

    elif accounting_type == 'Реализация':
        from_qs = StorageLocation.objects.filter(source_type='склад')
        to_qs = StorageLocation.objects.filter(source_type='контрагент')

    elif accounting_type == 'Списание':
        from_qs = StorageLocation.objects.filter(
            id__in=user_location_ids, source_type='склад'
        )
        to_qs = StorageLocation.objects.filter(
            id__in=user_location_ids
        ).exclude(source_type='контрагент')

    else:
        from_qs = StorageLocation.objects.none()
        to_qs = StorageLocation.objects.none()

    return (
        from_qs.distinct().order_by('source_type'),
        to_qs.distinct().order_by('source_type'),
    )


# ============================================================
# ПРЕДСТАВЛЕНИЯ
# ============================================================

@login_required
def conversion_shipping_create_view(request):
    """
    Шаг 1: отображает форму с общими полями и предзаполненной таблицей материалов.
    """
    position = _get_user_position(request)
    position_name = _get_user_position_name(request)
    if not position:
        messages.error(request, 'Не удалось определить должность пользователя')
        return redirect('inventory:conversion_list')

    # Получаем ID конвертаций из POST
    raw_ids = request.POST.get('conversion_ids', '')
    conversion_ids = _parse_conversion_ids(raw_ids)

    if not conversion_ids:
        messages.warning(request, 'Не выбрано ни одной конвертации')
        return redirect('inventory:conversion_list')

    user_location_ids = _get_user_location_ids(position)

    conversions = Conversion.objects.filter(
        id__in=conversion_ids
    ).select_related('target_material', 'storage_location')

    # Проверка прав: только свои склады
    allowed_conversions = []
    forbidden_ids = []
    for c in conversions:
        if c.storage_location.id in user_location_ids:
            allowed_conversions.append(c)
        else:
            forbidden_ids.append(c.id)

    if forbidden_ids:
        messages.error(
            request,
            f'Нет прав на конвертации № {", ".join(map(str, forbidden_ids))}'
        )

    if not allowed_conversions:
        return redirect('inventory:conversion_list')

    # ===== ПРОВЕРКА: все конвертации должны быть с одного склада =====
    unique_storage_ids = {c.storage_location_id for c in allowed_conversions}
    if len(unique_storage_ids) > 1:
        messages.error(
            request,
            'Нельзя массово отправить целевой материал сразу с двух складов. '
            'Выберите конвертации только с одного склада.'
        )
        return redirect('inventory:conversion_list')

    # Один склад — берём его объект
    common_storage_location = allowed_conversions[0].storage_location

    # Агрегируем целевые материалы
    aggregated_materials = _aggregate_target_materials(allowed_conversions)

    is_manager = (position_name and position_name.lower() == 'руководитель')

    all_choices = MaterialMovement.ACCOUNTING_TYPE_CHOICES
    if is_manager:
        accounting_choices = [c for c in all_choices if c[0] in ['Реализация', 'Отправление']]
    else:
        accounting_choices = [c for c in all_choices if c[0] != 'Реализация']

    driver_position = Position.objects.filter(name__iexact='водитель').first()
    if driver_position:
        drivers = Employee.objects.filter(
            position=driver_position, is_active=True
        ).order_by('last_name', 'first_name')
    else:
        drivers = Employee.objects.none()

    vehicles = Vehicle.objects.all().order_by('brand', 'model')

    now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')

    context = {
        'title': 'Отправка целевого материала из конвертаций',
        'employee_name': request.session.get('employee_name'),
        'position_name': position_name,
        'is_manager': is_manager,
        'accounting_choices': accounting_choices,
        'drivers': drivers,
        'vehicles': vehicles,
        'materials': aggregated_materials,
        'conversion_ids_str': ','.join(str(c.id) for c in allowed_conversions),
        'conversion_ids': [c.id for c in allowed_conversions],
        'conversions_count': len(allowed_conversions),
        'now_str': now_str,
        # НОВОЕ: склад, с которого отправляем (для предзаполнения "Откуда")
        'common_storage_location': common_storage_location,
        'common_storage_location_id': common_storage_location.id,
    }

    return render(request, 'MaterialMovement/conversion_shipping_create.html', context)


@login_required
def conversion_shipping_save_view(request):
    """
    Шаг 2: создаёт N движений материалов (по одному на каждый материал из таблицы).

    Общие поля: accounting_type, date_time, from_location, to_location,
                employee, vehicle, wagon_number
    Таблица: material_ids[], quantities_pieces[], quantities_meters[], quantities_cubic[]

    Для каждого материала создаётся отдельное движение и выполняется
    (для Перемещения / Реализации / Списания — сразу; для Отправления — ждёт подтверждения).
    """
    if request.method != 'POST':
        return redirect('inventory:conversion_list')

    position = _get_user_position(request)
    position_name = _get_user_position_name(request)
    if not position:
        messages.error(request, 'Не удалось определить должность пользователя')
        return redirect('inventory:conversion_list')

    # ===== 1. Читаем общие поля =====
    accounting_type = request.POST.get('accounting_type', '').strip()
    date_time_raw = request.POST.get('date_time', '').strip()
    from_location_id = request.POST.get('from_location', '').strip()
    to_location_id = request.POST.get('to_location', '').strip()
    employee_id = request.POST.get('employee', '').strip()
    vehicle_id = request.POST.get('vehicle', '').strip()
    wagon_number = request.POST.get('wagon_number', '').strip()

    # ===== 2. Валидация общих полей =====
    is_manager = (position_name and position_name.lower() == 'руководитель')

    if accounting_type not in dict(MaterialMovement.ACCOUNTING_TYPE_CHOICES):
        messages.error(request, 'Неверный тип движения')
        return redirect('inventory:conversion_list')

    if not is_manager and accounting_type == 'Реализация':
        messages.error(request, 'Только руководитель может создавать Реализацию')
        return redirect('inventory:conversion_list')

    if is_manager and accounting_type not in ['Реализация', 'Отправление']:
        messages.error(request, 'Руководителю доступны только Реализация и Отправление')
        return redirect('inventory:conversion_list')

    # Дата/время
    date_time = timezone.now()
    if date_time_raw:
        try:
            from datetime import datetime
            date_time = timezone.make_aware(
                datetime.strptime(date_time_raw, '%Y-%m-%dT%H:%M')
            )
        except (ValueError, TypeError):
            messages.error(request, 'Неверный формат даты и времени')
            return redirect('inventory:conversion_list')

    # Откуда
    if not from_location_id:
        messages.error(request, 'Укажите место хранения "Откуда"')
        return redirect('inventory:conversion_list')

    try:
        from_location = StorageLocation.objects.get(id=from_location_id)
    except StorageLocation.DoesNotExist:
        messages.error(request, 'Место хранения "Откуда" не найдено')
        return redirect('inventory:conversion_list')

    # Куда
    to_location = None
    if to_location_id:
        try:
            to_location = StorageLocation.objects.get(id=to_location_id)
        except StorageLocation.DoesNotExist:
            messages.error(request, 'Место хранения "Куда" не найдено')
            return redirect('inventory:conversion_list')

    # Водитель
    employee = None
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            pass

    # Транспорт
    vehicle = None
    if vehicle_id:
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            pass

    # ===== 3. Читаем таблицу материалов =====
    material_ids = request.POST.getlist('material_ids[]') or request.POST.getlist('material_ids')
    qty_pieces_list = request.POST.getlist('quantities_pieces[]') or request.POST.getlist('quantities_pieces')
    qty_meters_list = request.POST.getlist('quantities_meters[]') or request.POST.getlist('quantities_meters')
    qty_cubic_list = request.POST.getlist('quantities_cubic[]') or request.POST.getlist('quantities_cubic')
    conversion_ids_str = request.POST.get('conversion_ids', '')

    if not material_ids:
        messages.error(request, 'Таблица материалов пуста')
        return redirect('inventory:conversion_list')

    if not (len(material_ids) == len(qty_pieces_list) == len(qty_meters_list) == len(qty_cubic_list)):
        messages.error(request, 'Некорректные данные таблицы материалов')
        return redirect('inventory:conversion_list')

    def _to_decimal(value):
        """Безопасное преобразование в Decimal."""
        if value is None:
            return Decimal('0')
        value = str(value).strip().replace(',', '.')
        if not value:
            return Decimal('0')
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return Decimal('0')

    # ===== 4. Создаём движения =====
    created_movements = []
    errors = []

    # Заново загружаем конвертации, чтобы знать, какие материалы к ним относятся
    conversion_ids_list = _parse_conversion_ids(conversion_ids_str)
    conversions_map = {}  # material_id -> [conversion, ...]
    if conversion_ids_list:
        convs = Conversion.objects.filter(id__in=conversion_ids_list).select_related('target_material')
        for c in convs:
            conversions_map.setdefault(c.target_material_id, []).append(c)

    for idx, material_id in enumerate(material_ids):
        try:
            material = Material.objects.get(id=material_id)
        except (Material.DoesNotExist, ValueError, TypeError):
            errors.append(f'Материал с ID {material_id} не найден')
            continue

        qty_pieces = _to_decimal(qty_pieces_list[idx] if idx < len(qty_pieces_list) else '0')
        qty_meters = _to_decimal(qty_meters_list[idx] if idx < len(qty_meters_list) else '0')
        qty_cubic = _to_decimal(qty_cubic_list[idx] if idx < len(qty_cubic_list) else '0')

        if not (qty_pieces > 0 or qty_meters > 0 or qty_cubic > 0):
            errors.append(f'Материал "{material.name}": не указано количество')
            continue

        # Проверяем, что материал ещё не отправлялся из этих конвертаций
        related_conversions = conversions_map.get(int(material_id), [])
        already_shipped = [c for c in related_conversions if c.shipped_movement_id]
        if already_shipped:
            ids = ', '.join(str(c.id) for c in already_shipped)
            errors.append(
                f'Материал "{material.name}": конвертации № {ids} уже отправлены'
            )
            continue

        movement = MaterialMovement(
            accounting_type=accounting_type,
            date_time=date_time,
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=qty_pieces if qty_pieces > 0 else None,
            quantity_meters=qty_meters if qty_meters > 0 else None,
            quantity_cubic=qty_cubic if qty_cubic > 0 else None,
            employee=employee,
            vehicle=vehicle,
            wagon_number=wagon_number or None,
            created_by=request.user,
            created_by_position=position,
        )
        movement.save()

        # Выполняем движение
        if accounting_type in ['Перемещение', 'Реализация', 'Списание']:
            try:
                movement.execute_movement()
                # Привязываем конвертации к движению
                for c in related_conversions:
                    c.shipped_movement = movement
                    c.save(update_fields=['shipped_movement'])
                created_movements.append(movement)
            except ValueError as e:
                movement.delete()
                errors.append(f'"{material.name}": {str(e)}')
            except Exception as e:
                movement.delete()
                errors.append(f'"{material.name}": ошибка выполнения — {str(e)}')
        else:
            # Отправление — ждёт подтверждения
            for c in related_conversions:
                c.shipped_movement = movement
                c.save(update_fields=['shipped_movement'])
            created_movements.append(movement)

    # ===== 5. Итог =====
    if created_movements:
        messages.success(
            request,
            f'✅ Создано движений: {len(created_movements)} '
            f'(из {len(material_ids)} материалов)'
        )
    if errors:
        messages.warning(request, '⚠️ Ошибки: ' + '; '.join(errors))

    return redirect('inventory:material_movement_list')