# Forest_apps/inventory/services.py
from Forest_apps.inventory.models import StorageLocation
from Forest_apps.core.models import Warehouse, Brigade, Vehicle, Position


class StorageLocationService:
    """Сервис для работы с местами хранения"""

    @staticmethod
    def get_user_warehouses_by_position_name(position_name):
        """
        Получает склады пользователя по названию должности

        Args:
            position_name: название должности (из сессии)

        Returns:
            QuerySet StorageLocation (только склады)
        """
        if not position_name:
            return StorageLocation.objects.none()

        # Находим должность
        position = Position.objects.filter(name__iexact=position_name).first()
        if not position:
            return StorageLocation.objects.none()

        # Получаем все склады, созданные этой должностью
        warehouses = Warehouse.objects.filter(created_by_position=position)

        # Находим соответствующие StorageLocation
        location_ids = []
        for wh in warehouses:
            loc = StorageLocation.objects.filter(source_type='склад', source_id=wh.id).first()
            if loc:
                location_ids.append(loc.id)

        return StorageLocation.objects.filter(id__in=location_ids).order_by('source_type')

    @staticmethod
    def get_user_storage_locations_by_position_name(position_name, source_type=None):
        """
        Получает места хранения пользователя по названию должности

        Args:
            position_name: название должности (из сессии)
            source_type: тип места хранения ('склад', 'автомобиль', 'бригады', 'контрагент')

        Returns:
            QuerySet StorageLocation
        """
        if not position_name:
            return StorageLocation.objects.none()

        position = Position.objects.filter(name__iexact=position_name).first()
        if not position:
            return StorageLocation.objects.none()

        location_ids = []

        # Склады
        warehouses = Warehouse.objects.filter(created_by_position=position)
        for wh in warehouses:
            loc = StorageLocation.objects.filter(source_type='склад', source_id=wh.id).first()
            if loc:
                location_ids.append(loc.id)

        # Бригады
        brigades = Brigade.objects.filter(created_by_position=position)
        for br in brigades:
            loc = StorageLocation.objects.filter(source_type='бригады', source_id=br.id).first()
            if loc:
                location_ids.append(loc.id)

        # Транспорт
        vehicles = Vehicle.objects.filter(created_by_position=position)
        for vh in vehicles:
            loc = StorageLocation.objects.filter(source_type='автомобиль', source_id=vh.id).first()
            if loc:
                location_ids.append(loc.id)

        queryset = StorageLocation.objects.filter(id__in=location_ids)

        if source_type:
            queryset = queryset.filter(source_type=source_type)

        return queryset