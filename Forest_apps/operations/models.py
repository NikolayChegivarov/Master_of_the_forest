# Forest_apps/operations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

User = get_user_model()


# УЧЕТ ОПЕРАЦИЙ
class OperationType(models.Model):
    """Тип операции (технический процесс)"""
    name = models.CharField('Название', max_length=100)
    is_active = models.BooleanField('Активность', default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_operation_type'
    )
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='operation_type_created',
        null=True
    )

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

    @classmethod
    def get_active_operation_types(cls):
        """
        Получение всех активных типов операций
        """
        return cls.objects.filter(is_active=True).order_by('name')


class OperationRecord(models.Model):
    """Учет операций"""
    operation_type = models.ForeignKey(
        'operations.OperationType',
        on_delete=models.PROTECT,
        verbose_name='Операция'
    )
    date_time = models.DateTimeField('Дата/время', auto_now_add=True)
    warehouse = models.ForeignKey(
        'core.Warehouse',
        on_delete=models.PROTECT,
        verbose_name='Склад'
    )
    material = models.ForeignKey(
        'forestry.Material',
        on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    quantity = models.DecimalField(
        'Количество (шт)',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        help_text='Количество в штуках'
    )
    square_meters = models.DecimalField(
        'Площадь (м²)',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        null=True,
        blank=True,
        help_text='Площадь в квадратных метрах'
    )
    cubic_meters = models.DecimalField(
        'Объем (м³)',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        null=True,
        blank=True,
        help_text='Объем в кубических метрах'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто создал',
        related_name='created_operation_record'
    )
    created_by_position = models.ForeignKey(
        'core.Position',
        on_delete=models.PROTECT,
        verbose_name='Должность создателя',
        related_name='operation_record_created',
        null=True
    )

    class Meta:
        verbose_name = 'Запись операции'
        verbose_name_plural = 'Учет операций'
        indexes = [
            models.Index(fields=['date_time', 'operation_type']),
            models.Index(fields=['square_meters']),
            models.Index(fields=['cubic_meters']),
        ]

    def __str__(self):
        return f"{self.operation_type} - {self.date_time.date()}"

    @classmethod
    def create_operation_record(cls, operation_type, warehouse, material,
                                quantity, square_meters=None, cubic_meters=None, date_time=None):
        """
        Создание новой записи об операции с возможностью указания площади и объема
        """
        return cls.objects.create(
            operation_type=operation_type,
            warehouse=warehouse,
            material=material,
            quantity=quantity,
            square_meters=square_meters,
            cubic_meters=cubic_meters,
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
    def get_total_square_meters_by_material(cls, material_id, start_date=None, end_date=None):
        """
        Получение общей площади по материалу
        """
        from django.db.models import Sum

        queryset = cls.objects.filter(material_id=material_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        total = queryset.aggregate(total_square=Sum('square_meters'))['total_square']
        return total or 0

    @classmethod
    def get_total_cubic_meters_by_material(cls, material_id, start_date=None, end_date=None):
        """
        Получение общего объема по материалу
        """
        from django.db.models import Sum

        queryset = cls.objects.filter(material_id=material_id)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        total = queryset.aggregate(total_cubic=Sum('cubic_meters'))['total_cubic']
        return total or 0

    @classmethod
    def get_operations_summary(cls, start_date=None, end_date=None):
        """
        Получение сводки по операциям с учетом площади и объема
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
            total_square_meters=Sum('square_meters'),
            total_cubic_meters=Sum('cubic_meters'),
            operation_count=Count('id')
        ).order_by('operation_type__name', 'material__name')