# Forest_apps/employees/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings

# СОТРУДНИКИ И УЧЕТ РАБОЧЕГО ВРЕМЕНИ
class Employee(models.Model):
    """Сотрудник"""
    position = models.ForeignKey(
        'core.Position',  # СТРОКОВАЯ ССЫЛКА!
        on_delete=models.PROTECT,
        verbose_name='Должность'
    )
    warehouse = models.ForeignKey(
        'core.Warehouse',  # СТРОКОВАЯ ССЫЛКА!
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
    date_time = models.DateTimeField('Дата-время')
    warehouse = models.ForeignKey(
        'core.Warehouse',  # СТРОКОВАЯ ССЫЛКА!
        on_delete=models.PROTECT,
        verbose_name='Склад'
    )
    employee = models.ForeignKey(
        'employees.Employee',  # Внутри приложения - нормально
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
