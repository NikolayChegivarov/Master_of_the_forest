# Forest_apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    def create_position(cls, name, created_by=None, is_active=True):
        """
        Функция создания должности
        """
        return cls.objects.create(
            name=name,
            is_active=is_active,
            created_by=created_by
        )

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

    @classmethod
    def get_active_positions(cls):
        """
        Получение всех активных должностей
        """
        return cls.objects.filter(is_active=True).order_by('name')


class Warehouse(models.Model):
    """Склад"""
    name = models.CharField('Наименование', max_length=30)
    is_active = models.BooleanField('Активность', default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_warehouses'
    )
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='warehouses_created',
        null=True
    )

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического создания/обновления места хранения"""
        # Сначала сохраняем склад
        super().save(*args, **kwargs)

        # После сохранения создаем или обновляем место хранения
        self.update_storage_location()

    def update_storage_location(self):
        """Создание или обновление места хранения"""
        from Forest_apps.inventory.models import StorageLocation

        StorageLocation.objects.update_or_create(
            source_type='склад',
            source_id=self.id,
            defaults={'source_type': 'склад', 'source_id': self.id}
        )

    @classmethod
    def create_warehouse(cls, name, created_by=None, is_active=True):
        """
        Создание нового склада
        """
        warehouse = cls.objects.create(
            name=name,
            is_active=is_active,
            created_by=created_by
        )
        # Место хранения создается автоматически через save()
        return warehouse

    @classmethod
    def deactivate_warehouse(cls, warehouse_id):
        """
        Деактивация конкретного склада по ID
        """
        try:
            warehouse = cls.objects.get(id=warehouse_id)
            warehouse.is_active = False
            warehouse.save()
            # Место хранения остается, но склад деактивирован
            return warehouse
        except cls.DoesNotExist:
            raise ValueError(f"Склад с ID {warehouse_id} не найден")

    @classmethod
    def get_active_warehouses(cls):
        """
        Получение всех активных складов
        """
        return cls.objects.filter(is_active=True).order_by('name')


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
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='vehicles_created',
        null=True
    )

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'
        ordering = ['brand']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического создания/обновления места хранения"""
        # Сначала сохраняем ТС
        super().save(*args, **kwargs)

        # После сохранения создаем или обновляем место хранения
        self.update_storage_location()

    def update_storage_location(self):
        """Создание или обновление места хранения"""
        from Forest_apps.inventory.models import StorageLocation

        StorageLocation.objects.update_or_create(
            source_type='автомобиль',
            source_id=self.id,
            defaults={'source_type': 'автомобиль', 'source_id': self.id}
        )

    @classmethod
    def create_vehicle(cls, brand, model, license_plate, created_by=None, is_active=True):
        """
        Создание нового транспортного средства
        """
        vehicle = cls.objects.create(
            brand=brand,
            model=model,
            license_plate=license_plate,
            is_active=is_active,
            created_by=created_by
        )
        # Место хранения создается автоматически через save()
        return vehicle

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

    @classmethod
    def get_active_vehicles(cls):
        """
        Получение всех активных транспортных средств
        """
        return cls.objects.filter(is_active=True).order_by('brand', 'model')


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
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='counterparties_created',
        null=True
    )

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return f"{self.get_legal_form_display()} {self.name}"

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического создания/обновления места хранения"""
        # Сначала сохраняем контрагента
        super().save(*args, **kwargs)

        # После сохранения создаем или обновляем место хранения
        self.update_storage_location()

    def update_storage_location(self):
        """Создание или обновление места хранения"""
        from Forest_apps.inventory.models import StorageLocation

        StorageLocation.objects.update_or_create(
            source_type='контрагент',
            source_id=self.id,
            defaults={'source_type': 'контрагент', 'source_id': self.id}
        )

    @classmethod
    def create_counterparty(cls, legal_form, name, inn, ogrn, created_by=None, is_active=True):
        """
        Создание нового контрагента
        """
        counterparty = cls.objects.create(
            legal_form=legal_form,
            name=name,
            inn=inn,
            ogrn=ogrn,
            is_active=is_active,
            created_by=created_by
        )
        # Место хранения создается автоматически через save()
        return counterparty

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

    @classmethod
    def get_active_counterparties(cls):
        """
        Получение всех активных контрагентов
        """
        return cls.objects.filter(is_active=True).order_by('name')


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
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='brigades_created',
        null=True
    )

    class Meta:
        verbose_name = 'Бригада'
        verbose_name_plural = 'Бригады'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического создания/обновления места хранения"""
        # Сначала сохраняем бригаду
        super().save(*args, **kwargs)

        # После сохранения создаем или обновляем место хранения
        self.update_storage_location()

    def update_storage_location(self):
        """Создание или обновление места хранения"""
        from Forest_apps.inventory.models import StorageLocation

        StorageLocation.objects.update_or_create(
            source_type='бригады',
            source_id=self.id,
            defaults={'source_type': 'бригады', 'source_id': self.id}
        )

    @classmethod
    def create_brigade(cls, name, created_by=None, is_active=True):
        """
        Создание новой бригады
        """
        brigade = cls.objects.create(
            name=name,
            is_active=is_active,
            created_by=created_by
        )
        # Место хранения создается автоматически через save()
        return brigade

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

    @classmethod
    def get_active_brigades(cls):
        """
        Получение всех активных бригад
        """
        return cls.objects.filter(is_active=True).order_by('name')
