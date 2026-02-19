# Forest_apps/forestry/models.py
# Материалы/Лесосеки/Лесничества
from django.db import models
from django.core.validators import MinValueValidator


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
