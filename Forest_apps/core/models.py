# Forest_apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# ОСНОВНЫЕ СПРАВОЧНИКИ: должности/склады/ТС/бригада
class Position(models.Model):
    """Должность"""
    name = models.CharField('Наименование', max_length=30)
    is_active = models.BooleanField('Активность', default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_positions'
    )

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_position(cls, name, is_active=True):
        """
        Функция создания должности
        """
        return cls.objects.create(name=name, is_active=is_active)
    # Создание активной должности
    # position = Position.create_position(name="Водитель")

    @classmethod
    def get_active_positions(cls):
        """
        Получение всех активных должностей
        """
        return cls.objects.filter(is_active=True).order_by('name')
    # Получение всех активных должностей
    # active_positions = Position.get_active_positions()
    # for position in active_positions:
    #     print(position)

    @classmethod
    def deactivate_position(cls, position_id):
        """
        Деактивация конкретной должности по ID
        """
        try:
            position = cls.objects.get(id=position_id)
            position.is_active = False
            position.save()
            return position
        except cls.DoesNotExist:
            raise ValueError(f"Должность с ID {position_id} не найдена")


class Warehouse(models.Model):
    """Склад"""
    name = models.CharField('Наименование', max_length=30)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_warehouses'
    )

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_warehouse(cls, name, is_active=True):
        """
        Создание нового склада
        """
        return cls.objects.create(name=name, is_active=is_active)
    # Создание нового склада
    # warehouse = Warehouse.create_warehouse(name="Основной склад")

    @classmethod
    def deactivate_warehouse(cls, warehouse_id):
        """
        Деактивация конкретного склада по ID
        """
        try:
            warehouse = cls.objects.get(id=warehouse_id)
            warehouse.is_active = False
            warehouse.save()
            return warehouse
        except cls.DoesNotExist:
            raise ValueError(f"Склад с ID {warehouse_id} не найден")
    # Деактивация склада по ID
    # try:
    #     deactivated = Warehouse.deactivate_warehouse(warehouse_id=1)
    #     print(f"Склад '{deactivated.name}' деактивирован")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_warehouses(cls):
        """
        Получение всех активных складов
        """
        return cls.objects.filter(is_active=True).order_by('name')
    # Получение всех активных складов
    # active_warehouses = Warehouse.get_active_warehouses()
    # for warehouse in active_warehouses:
    #     print(warehouse)


class Vehicle(models.Model):
    """Транспортное средство"""
    brand = models.CharField('Марка', max_length=100)
    model = models.CharField('Модель', max_length=100)
    license_plate = models.CharField('Гос номер', max_length=20, unique=True)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_vehicles'
    )

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'
        ordering = ['brand']  # Исправлено с ['name'] на ['brand']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

    @classmethod
    def create_vehicle(cls, brand, model, license_plate, is_active=True):
        """
        Создание нового транспортного средства
        """
        return cls.objects.create(
            brand=brand,
            model=model,
            license_plate=license_plate,
            is_active=is_active
        )
    # Создание транспортного средства
    # vehicle = Vehicle.create_vehicle(
    #     brand="Toyota",
    #     model="Hilux",
    #     license_plate="А123ВС77",
    #     is_active=True
    # )

    @classmethod
    def deactivate_vehicle(cls, vehicle_id):
        """
        Деактивация конкретного транспортного средства по ID
        """
        try:
            vehicle = cls.objects.get(id=vehicle_id)
            vehicle.is_active = False
            vehicle.save()
            return vehicle
        except cls.DoesNotExist:
            raise ValueError(f"Транспортное средство с ID {vehicle_id} не найдено")
    # Деактивация транспортного средства по ID
    # try:
    #     deactivated = Vehicle.deactivate_vehicle(vehicle_id=1)
    #     print(f"ТС '{deactivated.brand} {deactivated.model}' деактивировано")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_vehicles(cls):
        """
        Получение всех активных транспортных средств
        """
        return cls.objects.filter(is_active=True).order_by('brand', 'model')
    # Получение всех активных ТС
    # active_vehicles = Vehicle.get_active_vehicles()
    # for vehicle in active_vehicles:
    #     print(vehicle)


class Counterparty(models.Model):
    """Контрагент"""
    LEGAL_FORM_CHOICES = [
        ('ООО', 'Общество с ограниченной ответственностью'),
        ('ИП', 'Индивидуальный предприниматель'),
    ]

    legal_form = models.CharField(
        'ОПФ',
        max_length=3,
        choices=LEGAL_FORM_CHOICES
    )
    name = models.CharField('Наименование', max_length=30)
    inn = models.CharField('ИНН', max_length=12, unique=True)
    ogrn = models.CharField('ОГРН', max_length=15, unique=True)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_counterparties'
    )

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return f"{self.get_legal_form_display()} {self.name}"

    @classmethod
    def create_counterparty(cls, legal_form, name, inn, ogrn, is_active=True):
        """
        Создание нового контрагента
        """
        return cls.objects.create(
            legal_form=legal_form,
            name=name,
            inn=inn,
            ogrn=ogrn,
            is_active=is_active
        )
    # Создание контрагента
    # counterparty = Counterparty.create_counterparty(
    #     legal_form='ООО',
    #     name='Лесная компания',
    #     inn='1234567890',
    #     ogrn='123456789012345',
    #     is_active=True
    # )

    @classmethod
    def deactivate_counterparty(cls, counterparty_id):
        """
        Деактивация конкретного контрагента по ID
        """
        try:
            counterparty = cls.objects.get(id=counterparty_id)
            counterparty.is_active = False
            counterparty.save()
            return counterparty
        except cls.DoesNotExist:
            raise ValueError(f"Контрагент с ID {counterparty_id} не найден")
    # Деактивация контрагента по ID
    # try:
    #     deactivated = Counterparty.deactivate_counterparty(counterparty_id=1)
    #     print(f"Контрагент '{deactivated.name}' деактивирован")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_counterparties(cls):
        """
        Получение всех активных контрагентов
        """
        return cls.objects.filter(is_active=True).order_by('name')
    # Получение всех активных контрагентов
    # active_counterparties = Counterparty.get_active_counterparties()
    # for counterparty in active_counterparties:
    #     print(counterparty)


class Brigade(models.Model):
    """Бригада"""
    name = models.CharField('Наименование', max_length=200)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_brigades'
    )

    class Meta:
        verbose_name = 'Бригада'
        verbose_name_plural = 'Бригады'

    def __str__(self):
        return self.name

    @classmethod
    def create_brigade(cls, name, is_active=True):
        """
        Создание новой бригады
        """
        return cls.objects.create(name=name, is_active=is_active)
    # Создание бригады
    # brigade = Brigade.create_brigade(name="Бригада лесорубов")

    @classmethod
    def deactivate_brigade(cls, brigade_id):
        """
        Деактивация конкретной бригады по ID
        """
        try:
            brigade = cls.objects.get(id=brigade_id)
            brigade.is_active = False
            brigade.save()
            return brigade
        except cls.DoesNotExist:
            raise ValueError(f"Бригада с ID {brigade_id} не найдена")
    # Деактивация бригады по ID
    # try:
    #     deactivated = Brigade.deactivate_brigade(brigade_id=1)
    #     print(f"Бригада '{deactivated.name}' деактивирована")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_brigades(cls):
        """
        Получение всех активных бригад
        """
        return cls.objects.filter(is_active=True).order_by('name')
    # Получение всех активных бригад
    # active_brigades = Brigade.get_active_brigades()
    # for brigade in active_brigades:
    #     print(brigade)