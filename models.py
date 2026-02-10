from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# ОСНОВНЫЕ СПРАВОЧНИКИ
class Position(models.Model):
    """Должность"""
    name = models.CharField('Наименование', max_length=30)
    is_active = models.BooleanField('Активность', default=True)

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


class Warehouse(models.Model):
    """Склад"""
    name = models.CharField('Наименование', max_length=30)
    is_active = models.BooleanField('Активность', default=True)

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


# СОТРУДНИКИ И УЧЕТ РАБОЧЕГО ВРЕМЕНИ
class Employee(models.Model):
    """Сотрудник"""
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        verbose_name='Должность'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Склад'
    )
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @classmethod
    def create_employee(cls, position, last_name, first_name, middle_name='',
                        warehouse=None, is_active=True):
        """
        Создание нового сотрудника
        """
        return cls.objects.create(
            position=position,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            warehouse=warehouse,
            is_active=is_active
        )
    # Создание сотрудника
    # position = Position.objects.get(name='Водитель')
    # warehouse = Warehouse.objects.get(name='Основной склад')
    # employee = Employee.create_employee(
    #     position=position,
    #     last_name='Иванов',
    #     first_name='Иван',
    #     middle_name='Иванович',
    #     warehouse=warehouse,
    #     is_active=True
    # )

    @classmethod
    def deactivate_employee(cls, employee_id):
        """
        Деактивация конкретного сотрудника по ID
        """
        try:
            employee = cls.objects.get(id=employee_id)
            employee.is_active = False
            employee.save()
            return employee
        except cls.DoesNotExist:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")
    # Деактивация сотрудника по ID
    # try:
    #     deactivated = Employee.deactivate_employee(employee_id=1)
    #     print(f"Сотрудник '{deactivated.full_name}' деактивирован")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_employees(cls):
        """
        Получение всех активных сотрудников
        """
        return cls.objects.filter(is_active=True).order_by('last_name', 'first_name')
    # Получение всех активных сотрудников
    # active_employees = Employee.get_active_employees()
    # for employee in active_employees:
    #     print(employee)

    @classmethod
    def get_employees_by_position(cls, position_name):
        """
        Получение сотрудников по названию должности
        """
        return cls.objects.filter(
            position__name__iexact=position_name,
            is_active=True
        ).order_by('last_name', 'first_name')
    # Получение водителей
    # drivers = Employee.get_employees_by_position('водитель')
    # for driver in drivers:
    #     print(driver)

    @classmethod
    def get_employees_by_warehouse(cls, warehouse_id):
        """
        Получение сотрудников по складу
        """
        return cls.objects.filter(
            warehouse_id=warehouse_id,
            is_active=True
        ).order_by('last_name', 'first_name')
    # Получение сотрудников склада
    # warehouse_employees = Employee.get_employees_by_warehouse(warehouse_id=1)
    # for employee in warehouse_employees:
    #     print(employee)


class WorkTimeRecord(models.Model):
    """Учет рабочего времени"""
    date_time = models.DateTimeField('Дата-время')
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name='Склад'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name='Сотрудник'
    )
    hours = models.DecimalField(
        'Количество часов',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Запись рабочего времени'
        verbose_name_plural = 'Учет рабочего времени'
        indexes = [
            models.Index(fields=['date_time', 'employee']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date_time.date()} - {self.hours} ч"

    @classmethod
    def create_work_time_record(cls, date_time, warehouse, employee, hours):
        """
        Создание новой записи рабочего времени

        Args:
            date_time: Дата и время работы (datetime)
            warehouse: Склад (Warehouse instance)
            employee: Сотрудник (Employee instance)
            hours: Количество часов (decimal)

        Returns:
            WorkTimeRecord instance
        """
        if hours < 0:
            raise ValueError("Часы не могут быть отрицательными")

        return cls.objects.create(
            date_time=date_time,
            warehouse=warehouse,
            employee=employee,
            hours=hours
        )

    # # Получаем объекты
    # warehouse = Warehouse.objects.get(name='Основной склад')
    # employee = Employee.objects.get(last_name='Иванов')
    #
    # # Создаём запись
    # record = WorkTimeRecord.create_work_time_record(
    #     date_time=timezone.now(),
    #     warehouse=warehouse,
    #     employee=employee,
    #     hours=8.5
    # )
    #
    # # Создание на конкретную дату
    # specific_time = datetime(2024, 1, 15, 9, 0, 0)
    # record = WorkTimeRecord.create_work_time_record(
    #     date_time=specific_time,
    #     warehouse=warehouse,
    #     employee=employee,
    #     hours=7.75
    # )

    @classmethod
    def get_records_by_employee(cls, employee_id, start_date=None, end_date=None):
        """
        Получение записей рабочего времени по сотруднику
        """
        queryset = cls.objects.filter(employee_id=employee_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.order_by('date_time')

    @classmethod
    def get_records_by_warehouse(cls, warehouse_id, date=None):
        """
        Получение записей рабочего времени по складу
        """
        queryset = cls.objects.filter(warehouse_id=warehouse_id)

        if date:
            queryset = queryset.filter(date_time__date=date)

        return queryset.order_by('date_time')

    @classmethod
    def get_total_hours_by_employee(cls, employee_id, start_date=None, end_date=None):
        """
        Получение общего количества часов по сотруднику
        """
        from django.db.models import Sum

        queryset = cls.objects.filter(employee_id=employee_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        total = queryset.aggregate(total_hours=Sum('hours'))['total_hours']
        return total or 0

# ЛЕСНИЧЕСТВА ЛЕСОСЕКИ МАТЕРИАЛЫ
class Material(models.Model):
    """Материал (Номенклатура)"""
    MATERIAL_TYPE_CHOICES = [
        ('древесина', 'Древесина'),
        ('ГСМ', 'ГСМ'),
        ('запчасти', 'Запчасти'),
    ]

    material_type = models.CharField(
        'Вид материала',
        max_length=20,
        choices=MATERIAL_TYPE_CHOICES
    )
    name = models.CharField('Номенклатура', max_length=200)

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        constraints = [
            models.UniqueConstraint(
                fields=['material_type', 'name'],
                name='unique_material_type_name'
            )
        ]

    def __str__(self):
        return f"{self.get_material_type_display()} - {self.name}"

    @classmethod
    def create_material(cls, material_type, name):
        """
        Создание нового материала
        """
        return cls.objects.create(material_type=material_type, name=name)
    # Создание материала
    # material = Material.create_material(
    #     material_type='древесина',
    #     name='Доска обрезная 50x150'
    # )

    @classmethod
    def get_materials_by_type(cls, material_type):
        """
        Получение материалов по типу
        """
        return cls.objects.filter(material_type=material_type).order_by('name')
    # Получение древесины
    # wood_materials = Material.get_materials_by_type('древесина')
    # for material in wood_materials:
    #     print(material)

    @classmethod
    def get_all_materials(cls):
        """
        Получение всех материалов с группировкой по типу
        """
        return cls.objects.all().order_by('material_type', 'name')
    # Получение всех материалов
    # all_materials = Material.get_all_materials()
    # for material in all_materials:
    #     print(material)


class Forestry(models.Model):
    """Лесничество"""
    name = models.CharField('Наименование', max_length=200)
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Лесничество'
        verbose_name_plural = 'Лесничества'

    def __str__(self):
        return self.name

    @classmethod
    def create_forestry(cls, name, is_active=True):
        """
        Создание нового лесничества
        """
        return cls.objects.create(name=name, is_active=is_active)

    @classmethod
    def deactivate_forestry(cls, forestry_id):
        """
        Деактивация конкретного лесничества по ID
        """
        try:
            forestry = cls.objects.get(id=forestry_id)
            forestry.is_active = False
            forestry.save()
            return forestry
        except cls.DoesNotExist:
            raise ValueError(f"Лесничество с ID {forestry_id} не найдено")

    @classmethod
    def get_active_forestries(cls):
        """
        Получение всех активных лесничеств
        """
        return cls.objects.filter(is_active=True).order_by('name')


class CuttingAreaContent(models.Model):
    """Содержание лесосеки"""
    cutting_area = models.ForeignKey(
        'CuttingArea',  # Используем строковую ссылку
        on_delete=models.CASCADE,
        verbose_name='Лесосека'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    quantity = models.DecimalField(
        'Количество',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Содержание лесосеки'
        verbose_name_plural = 'Содержание лесосек'
        constraints = [
            models.UniqueConstraint(
                fields=['cutting_area', 'material'],
                name='unique_cutting_area_material'
            )
        ]

    def __str__(self):
        return f"{self.cutting_area} - {self.material}: {self.quantity}"

    @classmethod
    def get_cutting_area_contents(cls, cutting_area_id):
        """
        Получение всего содержимого лесосеки
        """
        return cls.objects.filter(
            cutting_area_id=cutting_area_id
        ).select_related('material').order_by('material__material_type',
                                              'material__name')

    @classmethod
    def get_material_distribution(cls, material_id):
        """
        Получение распределения материала по лесосекам
        """
        return cls.objects.filter(
            material_id=material_id
        ).select_related('cutting_area', 'cutting_area__forestry').order_by(
            'cutting_area__forestry__name',
            'cutting_area__quarter_number',
            'cutting_area__division_number'
        )


class CuttingArea(models.Model):
    """Лесосека"""
    forestry = models.ForeignKey(
        Forestry,
        on_delete=models.PROTECT,
        verbose_name='Лесничество'
    )
    quarter_number = models.CharField('Номер квартала', max_length=20)
    division_number = models.CharField('Номер выдела', max_length=20)
    area_hectares = models.DecimalField(
        'Площадь выдела (Га)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField('Активность', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Лесосека'
        verbose_name_plural = 'Лесосеки'
        constraints = [
            models.UniqueConstraint(
                fields=['forestry', 'quarter_number', 'division_number'],
                name='unique_forestry_quarter_division'
            )
        ]

    def __str__(self):
        return f"{self.forestry} - кв.{self.quarter_number} - выд.{self.division_number}"

    @classmethod
    def create_cutting_area(cls, forestry, quarter_number, division_number,
                            area_hectares, is_active=True):
        """
        Создание новой лесосеки
        """
        return cls.objects.create(
            forestry=forestry,
            quarter_number=quarter_number,
            division_number=division_number,
            area_hectares=area_hectares,
            is_active=is_active
        )

    @classmethod
    def deactivate_cutting_area(cls, cutting_area_id):
        """
        Деактивация конкретной лесосеки по ID
        """
        try:
            cutting_area = cls.objects.get(id=cutting_area_id)
            cutting_area.is_active = False
            cutting_area.save()
            return cutting_area
        except cls.DoesNotExist:
            raise ValueError(f"Лесосека с ID {cutting_area_id} не найдена")

    @classmethod
    def get_active_cutting_areas(cls):
        """
        Получение всех активных лесосек
        """
        return cls.objects.filter(is_active=True).order_by('forestry__name',
                                                           'quarter_number',
                                                           'division_number')

    @classmethod
    def get_cutting_areas_by_forestry(cls, forestry_id):
        """
        Получение лесосек по лесничеству
        """
        return cls.objects.filter(
            forestry_id=forestry_id,
            is_active=True
        ).order_by('quarter_number', 'division_number')


    @classmethod
    def get_cutting_area_by_full_address(cls, forestry_name, quarter_number,
                                         division_number):
        """
        Получение лесосеки по полному адресу (лесничество + квартал + выдел)
        """
        try:
            return cls.objects.get(
                forestry__name__iexact=forestry_name,
                quarter_number=quarter_number,
                division_number=division_number,
                is_active=True
            )
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            raise ValueError(
                f"Найдено несколько лесосек с адресом: {forestry_name}, кв.{quarter_number}, выд.{division_number}")

    def update_material_quantity(self, material_id, quantity):
        """
        Добавление или обновление количества материала в лесосеке
        Возвращает кортеж (объект, создан_ли_новый)
        """
        try:
            # Пытаемся найти существующую запись
            content = CuttingAreaContent.objects.get(
                cutting_area=self,
                material_id=material_id
            )
            # Обновляем количество
            content.quantity = quantity
            content.save()
            return content, False  # (объект, не создан новый)
        except CuttingAreaContent.DoesNotExist:
            # Создаем новую запись
            content = CuttingAreaContent.objects.create(
                cutting_area=self,
                material_id=material_id,
                quantity=quantity
            )
            return content, True  # (объект, создан новый)
        except Exception as e:
            raise ValueError(f"Ошибка при обновлении материала: {str(e)}")

    def remove_material(self, material_id):
        """
        Удаление материала из лесосеки
        """
        try:
            content = CuttingAreaContent.objects.get(
                cutting_area=self,
                material_id=material_id
            )
            content.delete()
            return True
        except CuttingAreaContent.DoesNotExist:
            raise ValueError(f"Материал с ID {material_id} не найден в лесосеке {self}")

    def get_material_quantity(self, material_id):
        """
        Получение количества конкретного материала в лесосеке
        Возвращает 0 если материала нет
        """
        try:
            content = CuttingAreaContent.objects.get(
                cutting_area=self,
                material_id=material_id
            )
            return content.quantity
        except CuttingAreaContent.DoesNotExist:
            return 0

    def get_total_materials_quantity(self):
        """
        Получение общего количества всех материалов на лесосеке
        """
        total = CuttingAreaContent.objects.filter(
            cutting_area=self
        ).aggregate(
            total_quantity=models.Sum('quantity')
        )['total_quantity']

        return total or 0


    def get_all_materials(self):
        """
        Получение всех материалов лесосеки с их количеством
        """
        contents = CuttingAreaContent.objects.filter(
            cutting_area=self
        ).select_related('material').order_by('material__material_type', 'material__name')

        return [
            {
                'material': content.material,
                'quantity': content.quantity,
                'material_type': content.material.material_type,
                'material_type_display': content.material.get_material_type_display()
            }
            for content in contents
        ]

    @property
    def full_address(self):
        """
        Полный адрес лесосеки
        """
        return f"{self.forestry.name}, кв.{self.quarter_number}, выд.{self.division_number}"

    @property
    def materials_count(self):
        """
        Количество различных материалов в лесосеке
        """
        return CuttingAreaContent.objects.filter(cutting_area=self).count()


# МАТЕРИАЛЫ МЕСТА ХРАНЕНИЯ И ОСТАТКИ
class StorageLocation(models.Model):
    """Место хранения"""
    SOURCE_TYPE_CHOICES = [
        ('склад', 'Склад'),
        ('автомобиль', 'Автомобиль'),
        ('контрагент', 'Контрагент'),
        ('бригады', 'Бригада'),
    ]

    source_type = models.CharField(
        'Тип хранения',
        max_length=20,
        choices=SOURCE_TYPE_CHOICES
    )
    source_id = models.IntegerField('ID в исходной таблице')

    class Meta:
        verbose_name = 'Место хранения'
        verbose_name_plural = 'Места хранения'
        constraints = [
            models.UniqueConstraint(
                fields=['source_type', 'source_id'],
                name='unique_storage_location'
            )
        ]

    def __str__(self):
        # Вычисляемое поле для интерфейса
        source_name = self.get_source_name()
        return f"{self.get_source_type_display()}: {source_name}"

    def get_source_name(self):
        """Получить название источника"""
        if self.source_type == 'склад':
            try:
                return Warehouse.objects.get(pk=self.source_id).name
            except Warehouse.DoesNotExist:
                return f"Склад ID:{self.source_id}"
        elif self.source_type == 'автомобиль':
            try:
                vehicle = Vehicle.objects.get(pk=self.source_id)
                return f"{vehicle.brand} {vehicle.model} ({vehicle.license_plate})"
            except Vehicle.DoesNotExist:
                return f"Авто ID:{self.source_id}"
        elif self.source_type == 'контрагент':
            try:
                return Counterparty.objects.get(pk=self.source_id).name
            except Counterparty.DoesNotExist:
                return f"Контрагент ID:{self.source_id}"
        elif self.source_type == 'бригады':
            try:
                return Brigade.objects.get(pk=self.source_id).name
            except Brigade.DoesNotExist:
                return f"Бригада ID:{self.source_id}"
        return f"ID:{self.source_id}"


class MaterialMovement(models.Model):
    """Документ движения материалов"""
    ACCOUNTING_TYPE_CHOICES = [
        ('Перемещение', 'Перемещение'),
        ('Реализация', 'Реализация'),
        ('Списание', 'Списание'),
    ]

    date_time = models.DateTimeField('Дата/время', auto_now_add=True)
    accounting_type = models.CharField(
        'Тип учета',
        max_length=20,
        choices=ACCOUNTING_TYPE_CHOICES
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name='Сотрудник',
        limit_choices_to={'position__name__icontains': 'водитель'},
        null=True,
        blank=True
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        verbose_name='Транспортное средство',
        null=True,
        blank=True
    )
    from_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        verbose_name='Место хранения отправления',
        related_name='movements_from'
    )
    to_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        verbose_name='Место хранения назначения',
        related_name='movements_to',
        null=True,
        blank=True  # Для списаний может не быть получателя
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    quantity_pieces = models.DecimalField(
        'Количество в штуках',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=None
    )
    quantity_meters = models.DecimalField(
        'Количество в погонных метрах',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=None
    )
    quantity_cubic = models.DecimalField(
        'Количество в кубических метрах',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=None
    )
    price = models.DecimalField(
        'Цена за единицу',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=None
    )
    total_amount = models.DecimalField(
        'Сумма',
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=0
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Автор документа'
    )
    is_completed = models.BooleanField(
        'Выполнено',
        default=False,
        help_text='Движение завершено и остатки обновлены'
    )
    completed_at = models.DateTimeField(
        'Дата выполнения',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Документ движения материалов'
        verbose_name_plural = 'Документы движения материалов'
        indexes = [
            models.Index(fields=['date_time', 'accounting_type']),
            models.Index(fields=['from_location', 'to_location']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.accounting_type} №{self.id} от {self.date_time.date()}"

    def save(self, *args, **kwargs):
        """Метод сохранения с расчетом суммы только для Реализации"""
        if self.accounting_type == 'Реализация' and self.price:
            if self.quantity_pieces is not None:
                self.total_amount = self.quantity_pieces * self.price
            elif self.quantity_meters is not None:
                self.total_amount = self.quantity_meters * self.price
            elif self.quantity_cubic is not None:
                self.total_amount = self.quantity_cubic * self.price
            else:
                self.total_amount = 0
        else:
            # Для перемещения и списания сумма = 0
            self.total_amount = 0

        super().save(*args, **kwargs)

    @classmethod
    def create_movement(cls, accounting_type, from_location, to_location,
                        material, author, quantity_pieces=0, quantity_meters=None,
                        quantity_cubic=None, price=0, total_amount=0):
        """
        Базовый метод для создания документа движения материалов.
        Принимает все параметры движения и создаёт запись в базе данных.
        Является основой для create_transfer, create_sale, create_write_off.
        """
        return cls.objects.create(
            accounting_type=accounting_type,
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            price=price,
            total_amount=total_amount,
            author=author
        )

    def execute_movement(self):
        """
        Проводит документ движения.
        Выполнить движение - обновить остатки на основе документа.
        Возвращает кортеж (отправитель_остаток, получатель_остаток)
        Выполняется при условии, что is_completed переведен в состояние True
        """
        if self.is_completed:
            raise ValueError("Движение уже выполнено")

        # Проверяем обязательные поля в зависимости от типа
        if self.accounting_type == 'Перемещение' and not self.to_location:
            raise ValueError("Для перемещения необходимо указать получателя")

        # Для списания и реализации получатель может быть None
        # Создаем запись о выполнении
        from_balance, to_balance = MaterialBalance.process_movement(self)

        # Обновляем статус документа
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

        return from_balance, to_balance

    @classmethod
    def create_transfer(cls, from_location, to_location, material,
                       author, quantity_pieces=0, quantity_meters=None,
                       quantity_cubic=None):
        """
        Создание документа перемещения (без цены)
        """
        return cls.create_movement(
            accounting_type='Перемещение',
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            author=author,
            price=0,  # Перемещение без цены
            total_amount=0
        )

    @classmethod
    def create_sale(cls, from_location, to_location, material,
                    author, price, quantity_pieces=0, quantity_meters=None,
                    quantity_cubic=None):
        """
        Создание документа реализации (с ценой)
        """
        return cls.create_movement(
            accounting_type='Реализация',
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            price=price,  # Цена обязательна для реализации
            author=author
        )

    @classmethod
    def create_write_off(cls, from_location, to_location, material,
                        author, quantity_pieces=0, quantity_meters=None,
                        quantity_cubic=None):
        """
        Создание документа списания (без цены)
        """
        return cls.create_movement(
            accounting_type='Списание',
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            author=author,
            price=0,  # Списание без цены
            total_amount=0
        )

    def cancel_movement(self):
        """
        Отменить выполненное движение
        """
        if not self.is_completed:
            raise ValueError("Движение еще не выполнено")

        # Отменяем движение в остатках
        MaterialBalance.cancel_movement(self)

        # Обновляем статус документа
        self.is_completed = False
        self.completed_at = None
        self.save()

    @property
    def quantity_display(self):
        """Отображение количества"""
        parts = []
        if self.quantity_pieces:
            parts.append(f"{self.quantity_pieces} шт")
        if self.quantity_meters:
            parts.append(f"{self.quantity_meters} м.п.")
        if self.quantity_cubic:
            parts.append(f"{self.quantity_cubic} м³")
        return ", ".join(parts) if parts else "0"

    @classmethod
    def get_pending_movements(cls):
        """Получение невыполненных движений"""
        return cls.objects.filter(is_completed=False).order_by('date_time')

    @classmethod
    def get_completed_movements(cls, start_date=None, end_date=None):
        """Получение выполненных движений за период"""
        queryset = cls.objects.filter(is_completed=True)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.order_by('-date_time')


class MaterialBalance(models.Model):
    """Остатки материалов (без цены)"""
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        verbose_name='Место хранения'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    quantity_pieces = models.DecimalField(
        'Количество в штуках',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    quantity_meters = models.DecimalField(
        'Количество в погонных метрах',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=0
    )
    quantity_cubic = models.DecimalField(
        'Количество в кубических метрах',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=0
    )
    last_updated = models.DateTimeField(
        'Дата последнего обновления',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Остаток материала'
        verbose_name_plural = 'Остатки материалов'
        constraints = [
            models.UniqueConstraint(
                fields=['storage_location', 'material'],
                name='unique_material_balance'
            )
        ]
        indexes = [
            models.Index(fields=['storage_location', 'material']),
            models.Index(fields=['material', 'storage_location']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"{self.material}: {self.quantity_pieces} шт"

    def save(self, *args, **kwargs):
        """Просто сохраняем, без расчета суммы"""
        super().save(*args, **kwargs)

    @classmethod
    def process_movement(cls, movement):
        """
        Обработка документа движения - обновление остатков
        Возвращает (отправитель_остаток, получатель_остаток или None)
        """
        # Проверяем наличие на складе отправителя
        try:
            from_balance = cls.objects.get(
                storage_location=movement.from_location,
                material=movement.material
            )
        except cls.DoesNotExist:
            raise ValueError(f"Материал {movement.material} не найден в месте хранения {movement.from_location}")

        # Проверяем достаточность количества
        if movement.quantity_pieces and from_balance.quantity_pieces < movement.quantity_pieces:
            raise ValueError(
                f"Недостаточно материала в штуках: есть {from_balance.quantity_pieces}, требуется {movement.quantity_pieces}")

        if movement.quantity_meters and (from_balance.quantity_meters or 0) < movement.quantity_meters:
            raise ValueError(
                f"Недостаточно материала в погонных метрах: есть {from_balance.quantity_meters or 0}, требуется {movement.quantity_meters}")

        if movement.quantity_cubic and (from_balance.quantity_cubic or 0) < movement.quantity_cubic:
            raise ValueError(
                f"Недостаточно материала в кубических метрах: есть {from_balance.quantity_cubic or 0}, требуется {movement.quantity_cubic}")

        # Списываем с отправителя
        if movement.quantity_pieces:
            from_balance.quantity_pieces -= movement.quantity_pieces
        if movement.quantity_meters is not None:
            from_balance.quantity_meters = (from_balance.quantity_meters or 0) - (movement.quantity_meters or 0)
        if movement.quantity_cubic is not None:
            from_balance.quantity_cubic = (from_balance.quantity_cubic or 0) - (movement.quantity_cubic or 0)

        from_balance.save()

        # Для получателя (если есть)
        to_balance = None
        if movement.to_location:
            # ВАЖНО: Для списания не увеличиваем остатки у получателя!
            if movement.accounting_type != 'Списание':
                # Добавляем получателю только для перемещения и реализации
                to_balance, created = cls._add_to_balance(
                    storage_location=movement.to_location,
                    material=movement.material,
                    quantity_pieces=movement.quantity_pieces,
                    quantity_meters=movement.quantity_meters,
                    quantity_cubic=movement.quantity_cubic
                )

        return from_balance, to_balance

    @classmethod
    def cancel_movement(cls, movement):
        """
        Отмена документа движения - возврат остатков
        """
        # Возвращаем отправителю
        from_balance, _ = cls._add_to_balance(
            storage_location=movement.from_location,
            material=movement.material,
            quantity_pieces=movement.quantity_pieces,
            quantity_meters=movement.quantity_meters,
            quantity_cubic=movement.quantity_cubic
        )

        # Для получателя (если был и это не списание)
        if movement.to_location and movement.accounting_type != 'Списание':
            try:
                to_balance = cls.objects.get(
                    storage_location=movement.to_location,
                    material=movement.material
                )

                if movement.quantity_pieces:
                    to_balance.quantity_pieces -= movement.quantity_pieces
                if movement.quantity_meters is not None:
                    to_balance.quantity_meters = (to_balance.quantity_meters or 0) - (movement.quantity_meters or 0)
                if movement.quantity_cubic is not None:
                    to_balance.quantity_cubic = (to_balance.quantity_cubic or 0) - (movement.quantity_cubic or 0)

                to_balance.save()
            except cls.DoesNotExist:
                # Если получателя нет, пропускаем
                pass

        return from_balance

    @classmethod
    def _add_to_balance(cls, storage_location, material, quantity_pieces=0,
                        quantity_meters=None, quantity_cubic=None):
        """
        Внутренний метод: добавить материал на место хранения
        """
        try:
            balance = cls.objects.get(
                storage_location=storage_location,
                material=material
            )
            created = False

            if quantity_pieces:
                balance.quantity_pieces += quantity_pieces
            if quantity_meters is not None:
                balance.quantity_meters = (balance.quantity_meters or 0) + (quantity_meters or 0)
            if quantity_cubic is not None:
                balance.quantity_cubic = (balance.quantity_cubic or 0) + (quantity_cubic or 0)

            balance.save()

        except cls.DoesNotExist:
            balance = cls.objects.create(
                storage_location=storage_location,
                material=material,
                quantity_pieces=quantity_pieces,
                quantity_meters=quantity_meters,
                quantity_cubic=quantity_cubic
            )
            created = True

        return balance, created

    @classmethod
    def get_balance(cls, storage_location, material):
        """
        Получение остатка материала на месте хранения
        """
        try:
            return cls.objects.get(
                storage_location=storage_location,
                material=material
            )
        except cls.DoesNotExist:
            # Возвращаем нулевой объект (не сохраняем в БД)
            return cls(
                storage_location=storage_location,
                material=material,
                quantity_pieces=0,
                quantity_meters=0,
                quantity_cubic=0
            )

    @classmethod
    def get_storage_balances(cls, storage_location, material_type=None):
        """
        Получение всех остатков на месте хранения
        """
        queryset = cls.objects.filter(storage_location=storage_location)

        if material_type:
            queryset = queryset.filter(material__material_type=material_type)

        return queryset.select_related('material').order_by('material__material_type', 'material__name')

    @classmethod
    def get_material_total_balance(cls, material):
        """
        Получение общего остатка материала по всем местам хранения
        """
        result = cls.objects.filter(material=material).aggregate(
            total_pieces=models.Sum('quantity_pieces'),
            total_meters=models.Sum('quantity_meters'),
            total_cubic=models.Sum('quantity_cubic')
        )

        return {
            'material': material,
            'total_pieces': result['total_pieces'] or 0,
            'total_meters': result['total_meters'] or 0,
            'total_cubic': result['total_cubic'] or 0
        }

    @classmethod
    def get_balances_with_low_stock(cls, min_quantity=10, material_type=None):
        """
        Получение остатков с низким запасом
        """
        queryset = cls.objects.filter(quantity_pieces__lt=min_quantity)

        if material_type:
            queryset = queryset.filter(material__material_type=material_type)

        return queryset.select_related('material', 'storage_location').order_by('quantity_pieces')

    def has_sufficient_quantity(self, quantity_pieces=0, quantity_meters=0, quantity_cubic=0):
        """
        Проверка наличия достаточного количества материала
        """
        if quantity_pieces and self.quantity_pieces < quantity_pieces:
            return False
        if quantity_meters and (self.quantity_meters or 0) < quantity_meters:
            return False
        if quantity_cubic and (self.quantity_cubic or 0) < quantity_cubic:
            return False
        return True

    @property
    def quantity_display(self):
        """Отображение количества"""
        parts = []
        if self.quantity_pieces:
            parts.append(f"{self.quantity_pieces} шт")
        if self.quantity_meters:
            parts.append(f"{self.quantity_meters} м.п.")
        if self.quantity_cubic:
            parts.append(f"{self.quantity_cubic} м³")
        return ", ".join(parts) if parts else "0"


# УЧЕТ ОПЕРАЦИЙ
class OperationType(models.Model):
    """Тип операции (техпроцесс)"""
    name = models.CharField('Название', max_length=100)
    is_active = models.BooleanField('Активность', default=True)

    class Meta:
        verbose_name = 'Тип операции'
        verbose_name_plural = 'Типы операций'

    def __str__(self):
        return self.name

    @classmethod
    def create_operation_type(cls, name, is_active=True):
        """
        Создание нового типа операции
        """
        return cls.objects.create(name=name, is_active=is_active)
    # Создание типа операции
    # operation_type = OperationType.create_operation_type(name='Распиловка')

    @classmethod
    def deactivate_operation_type(cls, operation_type_id):
        """
        Деактивация конкретного типа операции по ID
        """
        try:
            operation_type = cls.objects.get(id=operation_type_id)
            operation_type.is_active = False
            operation_type.save()
            return operation_type
        except cls.DoesNotExist:
            raise ValueError(f"Тип операции с ID {operation_type_id} не найден")
    # Деактивация типа операции по ID
    # try:
    #     deactivated = OperationType.deactivate_operation_type(operation_type_id=1)
    #     print(f"Тип операции '{deactivated.name}' деактивирован")
    # except ValueError as e:
    #     print(e)

    @classmethod
    def get_active_operation_types(cls):
        """
        Получение всех активных типов операций
        """
        return cls.objects.filter(is_active=True).order_by('name')
    # Получение всех активных типов операций
    # active_operation_types = OperationType.get_active_operation_types()
    # for operation_type in active_operation_types:
    #     print(operation_type)


class OperationRecord(models.Model):
    """Учет операций"""
    operation_type = models.ForeignKey(
        OperationType,
        on_delete=models.PROTECT,
        verbose_name='Операция'
    )
    date_time = models.DateTimeField('Дата/время', auto_now_add=True)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        verbose_name='Склад'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    quantity = models.DecimalField(
        'Количество',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)]
    )

    class Meta:
        verbose_name = 'Запись операции'
        verbose_name_plural = 'Учет операций'
        indexes = [
            models.Index(fields=['date_time', 'operation_type']),
        ]

    def __str__(self):
        return f"{self.operation_type} - {self.date_time.date()}"

    @classmethod
    def create_operation_record(cls, operation_type, warehouse, material,
                                quantity, date_time=None):
        """
        Создание новой записи об операции

        Args:
            operation_type: Тип операции (OperationType instance)
            warehouse: Склад (Warehouse instance)
            material: Материал (Material instance)
            quantity: Количество (decimal)
            date_time: Дата/время операции (optional)

        Returns:
            OperationRecord instance
        """
        return cls.objects.create(
            operation_type=operation_type,
            warehouse=warehouse,
            material=material,
            quantity=quantity,
            date_time=date_time if date_time else timezone.now()
        )

    @classmethod
    def get_records_by_operation_type(cls, operation_type_id, start_date=None, end_date=None):
        """
        Получение записей операций по типу операции
        """
        queryset = cls.objects.filter(operation_type_id=operation_type_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.order_by('date_time')

    @classmethod
    def get_records_by_material(cls, material_id, start_date=None, end_date=None):
        """
        Получение записей операций по материалу
        """
        queryset = cls.objects.filter(material_id=material_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.order_by('date_time')

    @classmethod
    def get_total_quantity_by_material(cls, material_id, start_date=None, end_date=None):
        """
        Получение общего количества обработанного материала
        """
        from django.db.models import Sum

        queryset = cls.objects.filter(material_id=material_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        total = queryset.aggregate(total_quantity=Sum('quantity'))['total_quantity']
        return total or 0

    @classmethod
    def get_operations_summary(cls, start_date=None, end_date=None):
        """
        Получение сводки по операциям
        """
        from django.db.models import Sum, Count

        queryset = cls.objects.all()

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.values(
            'operation_type__name',
            'material__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            operation_count=Count('id')
        ).order_by('operation_type__name', 'material__name')

