# Forest_apps/inventory/services.py
from django.db.models import Q
from Forest_apps.inventory.models import StorageLocation
from Forest_apps.core.models import Warehouse, Brigade, Vehicle, Position


class StorageLocationService:
    """Сервис для работы с местами хранения"""

    # ============================================================
    # МЕТОДЫ ПО ПОЛЬЗОВАТЕЛЮ (created_by)
    # ============================================================

    @staticmethod
    def get_user_storage_locations(user, source_type=None):
        """Получает места хранения пользователя (по created_by)."""
        if not user or not user.is_authenticated:
            return StorageLocation.objects.none()

        wh_ids = list(Warehouse.objects.filter(created_by=user).values_list('id', flat=True))
        br_ids = list(Brigade.objects.filter(created_by=user).values_list('id', flat=True))
        vh_ids = list(Vehicle.objects.filter(created_by=user).values_list('id', flat=True))

        return StorageLocationService._filter_locations_by_ids(
            wh_ids, br_ids, vh_ids, source_type
        )

    @staticmethod
    def get_user_warehouses(user):
        return StorageLocationService.get_user_storage_locations(user, source_type='склад')

    @staticmethod
    def get_user_vehicles(user):
        return StorageLocationService.get_user_storage_locations(user, source_type='автомобиль')

    @staticmethod
    def get_user_brigades(user):
        return StorageLocationService.get_user_storage_locations(user, source_type='бригады')

    # ============================================================
    # МЕТОДЫ ПО НАЗВАНИЮ ДОЛЖНОСТИ
    # ============================================================

    @staticmethod
    def get_user_warehouses_by_position_name(position_name):
        """Получает склады по названию должности."""
        if not position_name:
            return StorageLocation.objects.none()

        position = Position.objects.filter(name__iexact=position_name).first()
        if not position:
            return StorageLocation.objects.none()

        wh_ids = list(Warehouse.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        if not wh_ids:
            return StorageLocation.objects.none()

        return StorageLocation.objects.filter(
            source_type='склад',
            source_id__in=wh_ids
        ).order_by('source_type')

    @staticmethod
    def get_user_storage_locations_by_position_name(position_name, source_type=None):
        """Получает места хранения по названию должности."""
        if not position_name:
            return StorageLocation.objects.none()

        position = Position.objects.filter(name__iexact=position_name).first()
        if not position:
            return StorageLocation.objects.none()

        wh_ids = list(Warehouse.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        br_ids = list(Brigade.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        vh_ids = list(Vehicle.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        return StorageLocationService._filter_locations_by_ids(
            wh_ids, br_ids, vh_ids, source_type
        )

    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЙ МЕТОД
    # ============================================================

    @staticmethod
    def _filter_locations_by_ids(warehouse_ids, brigade_ids, vehicle_ids, source_type=None):
        """Формирует queryset мест хранения по спискам ID (один запрос)."""
        q = Q()
        has_filter = False

        if warehouse_ids and (not source_type or source_type == 'склад'):
            q |= Q(source_type='склад', source_id__in=warehouse_ids)
            has_filter = True
        if brigade_ids and (not source_type or source_type == 'бригады'):
            q |= Q(source_type='бригады', source_id__in=brigade_ids)
            has_filter = True
        if vehicle_ids and (not source_type or source_type == 'автомобиль'):
            q |= Q(source_type='автомобиль', source_id__in=vehicle_ids)
            has_filter = True

        if not has_filter:
            return StorageLocation.objects.none()

        return StorageLocation.objects.filter(q).order_by('source_type')

    # ============================================================
    # ОПРЕДЕЛЕНИЕ ПРАВ (без запросов к БД при повторном вызове)
    # ============================================================

    @staticmethod
    def get_user_position_ownership_ids(position_name):
        """
        Возвращает словарь с ID объектов, принадлежащих должности.
        Используется для определения роли пользователя без N+1.

        Returns:
            dict: {
                'position_id': int | None,
                'warehouse_ids': set,
                'brigade_ids': set,
                'vehicle_ids': set,
                'all_location_ids': set,
            }
        """
        result = {
            'position_id': None,
            'warehouse_ids': set(),
            'brigade_ids': set(),
            'vehicle_ids': set(),
            'all_location_ids': set(),
        }

        if not position_name:
            return result

        position = Position.objects.filter(name__iexact=position_name).first()
        if not position:
            return result

        result['position_id'] = position.id

        result['warehouse_ids'] = set(Warehouse.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        result['brigade_ids'] = set(Brigade.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        result['vehicle_ids'] = set(Vehicle.objects.filter(
            created_by_position=position
        ).values_list('id', flat=True))

        # ID всех StorageLocation, принадлежащих должности (один запрос)
        if result['warehouse_ids'] or result['brigade_ids'] or result['vehicle_ids']:
            result['all_location_ids'] = set(StorageLocation.objects.filter(
                Q(source_type='склад', source_id__in=result['warehouse_ids']) |
                Q(source_type='бригады', source_id__in=result['brigade_ids']) |
                Q(source_type='автомобиль', source_id__in=result['vehicle_ids'])
            ).values_list('id', flat=True))

        return result