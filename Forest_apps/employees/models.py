# Forest_apps/employees/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


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
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_employees'
    )

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

    @property
    def short_name(self):
        """Короткое имя (Фамилия И.О.)"""
        initials = ''
        if self.first_name:
            initials += self.first_name[0] + '.'
        if self.middle_name:
            initials += self.middle_name[0] + '.'
        return f"{self.last_name} {initials}".strip()

    @classmethod
    def create_employee(cls, position, last_name, first_name, middle_name='',
                        warehouse=None, created_by=None, is_active=True):
        """
        Создание нового сотрудника
        """
        return cls.objects.create(
            position=position,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            warehouse=warehouse,
            is_active=is_active,
            created_by=created_by
        )

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

    @classmethod
    def get_active_employees(cls):
        """
        Получение всех активных сотрудников
        """
        return cls.objects.filter(is_active=True).order_by('last_name', 'first_name')

    @classmethod
    def get_employees_by_position(cls, position_name):
        """
        Получение сотрудников по названию должности
        """
        return cls.objects.filter(
            position__name__iexact=position_name,
            is_active=True
        ).order_by('last_name', 'first_name')

    @classmethod
    def get_employees_by_warehouse(cls, warehouse_id):
        """
        Получение сотрудников по складу
        """
        return cls.objects.filter(
            warehouse_id=warehouse_id,
            is_active=True
        ).order_by('last_name', 'first_name')


class WorkTimeRecord(models.Model):
    """Запись рабочего времени"""
    date_time = models.DateTimeField('Дата-время')
    warehouse = models.ForeignKey(
        'core.Warehouse',  # СТРОКОВАЯ ССЫЛКА!
        on_delete=models.PROTECT,
        verbose_name='Склад'
    )
    employee = models.ForeignKey(
        Employee,  # Можно использовать прямой импорт
        on_delete=models.PROTECT,
        verbose_name='Сотрудник'
    )
    hours = models.DecimalField(
        'Количество часов',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_worktimerecords'
    )

    class Meta:
        verbose_name = 'Запись рабочего времени'
        verbose_name_plural = 'Учет рабочего времени'
        indexes = [
            models.Index(fields=['date_time', 'employee']),
        ]

    def __str__(self):
        return f"{self.employee.short_name} - {self.date_time.date()} - {self.hours} ч"

    @classmethod
    def create_work_time_record(cls, date_time, warehouse, employee, hours, created_by=None):
        """
        Создание новой записи рабочего времени

        Args:
            date_time: Дата и время работы (datetime)
            warehouse: Склад (Warehouse instance)
            employee: Сотрудник (Employee instance)
            hours: Количество часов (decimal)
            created_by: Кто создал запись (User instance)

        Returns:
            WorkTimeRecord instance
        """
        if hours < 0:
            raise ValueError("Часы не могут быть отрицательными")

        return cls.objects.create(
            date_time=date_time,
            warehouse=warehouse,
            employee=employee,
            hours=hours,
            created_by=created_by
        )

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
    def get_records_by_creator(cls, user_id, start_date=None, end_date=None):
        """
        Получение записей, созданных конкретным пользователем
        """
        queryset = cls.objects.filter(created_by_id=user_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.order_by('-created_at')

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

    @classmethod
    def get_total_hours_by_warehouse(cls, warehouse_id, date=None):
        """
        Получение общего количества часов по складу за дату
        """
        from django.db.models import Sum

        queryset = cls.objects.filter(warehouse_id=warehouse_id)

        if date:
            queryset = queryset.filter(date_time__date=date)

        total = queryset.aggregate(total_hours=Sum('hours'))['total_hours']
        return total or 0