# Forest_apps/inventory/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.apps import apps  # Для get_model
from django.contrib.auth import get_user_model

User = get_user_model()


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
        source_name = self.get_source_name()
        return f"{self.get_source_type_display()}: {source_name}"

    def get_source_name(self):
        """Получить название источника"""
        model_map = {
            'склад': {
                'app': 'core',
                'model': 'Warehouse',
                'formatter': lambda obj: obj.name
            },
            'автомобиль': {
                'app': 'core',
                'model': 'Vehicle',
                'formatter': lambda obj: f"{obj.brand} {obj.model} ({obj.license_plate})"
            },
            'контрагент': {
                'app': 'core',
                'model': 'Counterparty',
                'formatter': lambda obj: obj.name
            },
            'бригады': {
                'app': 'core',
                'model': 'Brigade',
                'formatter': lambda obj: obj.name
            }
        }

        source_config = model_map.get(self.source_type)
        if not source_config:
            return f"Неизвестный тип: {self.source_type} ID:{self.source_id}"

        try:
            Model = apps.get_model(
                app_label=source_config['app'],
                model_name=source_config['model']
            )
            source_object = Model.objects.get(pk=self.source_id)
            return source_config['formatter'](source_object)

        except LookupError:
            return f"Ошибка: модель {source_config['app']}.{source_config['model']} не найдена"
        except Model.DoesNotExist:
            return f"{source_config['model']} ID:{self.source_id} (не найден)"
        except Exception as e:
            return f"Ошибка получения {self.source_type}: {str(e)}"


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

    # ✅ Правильные строковые ссылки
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.PROTECT,
        verbose_name='Сотрудник',
        limit_choices_to={'position__name__icontains': 'водитель'},
        null=True,
        blank=True
    )

    vehicle = models.ForeignKey(
        'core.Vehicle',
        on_delete=models.PROTECT,
        verbose_name='Транспортное средство',
        null=True,
        blank=True
    )

    from_location = models.ForeignKey(
        'inventory.StorageLocation',
        on_delete=models.PROTECT,
        verbose_name='Место хранения отправления',
        related_name='movements_from'
    )

    to_location = models.ForeignKey(
        'inventory.StorageLocation',
        on_delete=models.PROTECT,
        verbose_name='Место хранения назначения',
        related_name='movements_to',
        null=True,
        blank=True
    )

    material = models.ForeignKey(
        'forestry.Material',
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
            self.total_amount = 0

        super().save(*args, **kwargs)

    @classmethod
    def create_movement(cls, accounting_type, from_location, to_location,
                        material, author, quantity_pieces=0, quantity_meters=None,
                        quantity_cubic=None, price=0, total_amount=0):
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
        if self.is_completed:
            raise ValueError("Движение уже выполнено")

        if self.accounting_type == 'Перемещение' and not self.to_location:
            raise ValueError("Для перемещения необходимо указать получателя")

        MaterialBalance = apps.get_model('inventory', 'MaterialBalance')
        from_balance, to_balance = MaterialBalance.process_movement(self)

        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

        return from_balance, to_balance

    @classmethod
    def create_transfer(cls, from_location, to_location, material,
                        author, quantity_pieces=0, quantity_meters=None,
                        quantity_cubic=None):
        return cls.create_movement(
            accounting_type='Перемещение',
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            author=author,
            price=0,
            total_amount=0
        )

    @classmethod
    def create_sale(cls, from_location, to_location, material,
                    author, price, quantity_pieces=0, quantity_meters=None,
                    quantity_cubic=None):
        return cls.create_movement(
            accounting_type='Реализация',
            from_location=from_location,
            to_location=to_location,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            price=price,
            author=author
        )

    @classmethod
    def create_write_off(cls, from_location, material,
                         author, quantity_pieces=0, quantity_meters=None,
                         quantity_cubic=None):
        return cls.create_movement(
            accounting_type='Списание',
            from_location=from_location,
            to_location=None,
            material=material,
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            author=author,
            price=0,
            total_amount=0
        )

    def cancel_movement(self):
        if not self.is_completed:
            raise ValueError("Движение еще не выполнено")

        MaterialBalance = apps.get_model('inventory', 'MaterialBalance')
        MaterialBalance.cancel_movement(self)

        self.is_completed = False
        self.completed_at = None
        self.save()

    @property
    def quantity_display(self):
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
        return cls.objects.filter(is_completed=False).order_by('date_time')

    @classmethod
    def get_completed_movements(cls, start_date=None, end_date=None):
        queryset = cls.objects.filter(is_completed=True)

        if start_date:
            queryset = queryset.filter(date_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_time__lte=end_date)

        return queryset.order_by('-date_time')


class MaterialBalance(models.Model):
    """Остатки материалов (без цены)"""
    storage_location = models.ForeignKey(
        'inventory.StorageLocation',
        on_delete=models.PROTECT,
        verbose_name='Место хранения'
    )
    material = models.ForeignKey(
        'forestry.Material',
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

    @classmethod
    def process_movement(cls, movement):
        try:
            from_balance = cls.objects.get(
                storage_location=movement.from_location,
                material=movement.material
            )
        except cls.DoesNotExist:
            raise ValueError(f"Материал {movement.material} не найден в месте хранения {movement.from_location}")

        if movement.quantity_pieces and from_balance.quantity_pieces < movement.quantity_pieces:
            raise ValueError(
                f"Недостаточно материала в штуках: есть {from_balance.quantity_pieces}, требуется {movement.quantity_pieces}")

        if movement.quantity_meters and (from_balance.quantity_meters or 0) < movement.quantity_meters:
            raise ValueError(
                f"Недостаточно материала в погонных метрах: есть {from_balance.quantity_meters or 0}, требуется {movement.quantity_meters}")

        if movement.quantity_cubic and (from_balance.quantity_cubic or 0) < movement.quantity_cubic:
            raise ValueError(
                f"Недостаточно материала в кубических метрах: есть {from_balance.quantity_cubic or 0}, требуется {movement.quantity_cubic}")

        if movement.quantity_pieces:
            from_balance.quantity_pieces -= movement.quantity_pieces
        if movement.quantity_meters is not None:
            from_balance.quantity_meters = (from_balance.quantity_meters or 0) - (movement.quantity_meters or 0)
        if movement.quantity_cubic is not None:
            from_balance.quantity_cubic = (from_balance.quantity_cubic or 0) - (movement.quantity_cubic or 0)

        from_balance.save()

        to_balance = None
        if movement.to_location and movement.accounting_type != 'Списание':
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
        from_balance, _ = cls._add_to_balance(
            storage_location=movement.from_location,
            material=movement.material,
            quantity_pieces=movement.quantity_pieces,
            quantity_meters=movement.quantity_meters,
            quantity_cubic=movement.quantity_cubic
        )

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
                pass

        return from_balance

    @classmethod
    def _add_to_balance(cls, storage_location, material, quantity_pieces=0,
                        quantity_meters=None, quantity_cubic=None):
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
        try:
            return cls.objects.get(
                storage_location=storage_location,
                material=material
            )
        except cls.DoesNotExist:
            return cls(
                storage_location=storage_location,
                material=material,
                quantity_pieces=0,
                quantity_meters=0,
                quantity_cubic=0
            )

    @classmethod
    def get_storage_balances(cls, storage_location, material_type=None):
        queryset = cls.objects.filter(storage_location=storage_location)

        if material_type:
            queryset = queryset.filter(material__material_type=material_type)

        return queryset.select_related('material').order_by('material__material_type', 'material__name')

    @classmethod
    def get_material_total_balance(cls, material):
        from django.db import models
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
        queryset = cls.objects.filter(quantity_pieces__lt=min_quantity)

        if material_type:
            queryset = queryset.filter(material__material_type=material_type)

        return queryset.select_related('material', 'storage_location').order_by('quantity_pieces')

    def has_sufficient_quantity(self, quantity_pieces=0, quantity_meters=0, quantity_cubic=0):
        if quantity_pieces and self.quantity_pieces < quantity_pieces:
            return False
        if quantity_meters and (self.quantity_meters or 0) < quantity_meters:
            return False
        if quantity_cubic and (self.quantity_cubic or 0) < quantity_cubic:
            return False
        return True

    @property
    def quantity_display(self):
        parts = []
        if self.quantity_pieces:
            parts.append(f"{self.quantity_pieces} шт")
        if self.quantity_meters:
            parts.append(f"{self.quantity_meters} м.п.")
        if self.quantity_cubic:
            parts.append(f"{self.quantity_cubic} м³")
        return ", ".join(parts) if parts else "0"