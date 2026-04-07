from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from Forest_apps.inventory.models import MaterialBalance, StorageLocation, Receipt
from Forest_apps.forestry.models import Material
from Forest_apps.core.models import Warehouse, Brigade, Vehicle
from Forest_apps.inventory.services import StorageLocationService


class MaterialBalanceFilterForm(forms.Form):
    """Форма фильтрации остатков материалов"""
    storage_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.all().order_by('source_type'),
        required=False,
        label='Место хранения',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + Material.MATERIAL_TYPE_CHOICES,
        required=False,
        label='Тип материала',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material = forms.ModelChoiceField(
        queryset=Material.objects.all().order_by('name'),
        required=False,
        label='Материал',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.data.get('material_type'):
            self.fields['material'].queryset = Material.objects.filter(
                material_type=self.data.get('material_type')
            ).order_by('name')


class MaterialBalanceCreateForm(forms.ModelForm):
    """Форма создания/редактирования остатка материала (создает также поступление)"""

    receipt_date = forms.DateTimeField(
        label='Дата поступления',
        initial=timezone.now,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        required=True
    )

    source_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.filter(source_type='контрагент'),
        required=False,
        label='Источник поступления (контрагент)',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    price = forms.DecimalField(
        label='Цена за единицу',
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Цена за единицу',
            'step': '0.01',
            'min': '0'
        })
    )

    class Meta:
        model = MaterialBalance
        fields = ['storage_location', 'material', 'quantity_pieces', 'quantity_meters', 'quantity_cubic']
        widgets = {
            'storage_location': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в штуках',
                'step': '0.001',
                'min': '0'
            }),
            'quantity_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в погонных метрах',
                'step': '0.001',
                'min': '0'
            }),
            'quantity_cubic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в кубических метрах',
                'step': '0.001',
                'min': '0'
            }),
        }
        labels = {
            'storage_location': 'Место хранения (склад)',
            'material': 'Материал',
            'quantity_pieces': 'Штуки',
            'quantity_meters': 'Погонные метры',
            'quantity_cubic': 'Кубические метры',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.position_name = kwargs.pop('position_name', None)
        self.receipt_instance = kwargs.pop('receipt_instance', None)
        super().__init__(*args, **kwargs)

        # Получаем склады через сервис
        user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(
            self.position_name
        )

        self.fields['storage_location'].queryset = user_warehouses
        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')

        # Источник поступления - только контрагенты
        self.fields['source_location'].queryset = StorageLocation.objects.filter(
            source_type='контрагент'
        ).order_by('source_type')

        # Если редактируем поступление, подставляем данные
        if self.receipt_instance:
            self.initial['receipt_date'] = self.receipt_instance.receipt_date
            self.initial['source_location'] = self.receipt_instance.source_location
            self.initial['price'] = self.receipt_instance.price
            self.initial['quantity_pieces'] = self.receipt_instance.quantity_pieces
            self.initial['quantity_meters'] = self.receipt_instance.quantity_meters
            self.initial['quantity_cubic'] = self.receipt_instance.quantity_cubic
            self.initial['storage_location'] = self.receipt_instance.storage_location.id
            self.initial['material'] = self.receipt_instance.material.id

    def _get_user_warehouse_ids(self):
        """Получает ID складов (StorageLocation), доступных для должности пользователя"""
        from Forest_apps.core.models import Position, Warehouse
        from Forest_apps.inventory.models import StorageLocation

        if not self.user or not self.user.is_authenticated:
            return []

        position_name = self.position_name

        if not position_name:
            return []

        # Ищем должность (регистронезависимо)
        position = Position.objects.filter(name__iexact=position_name).first()

        if not position:
            return []

        # Получаем все склады с этой должностью
        warehouses = Warehouse.objects.filter(created_by_position=position)

        # Находим соответствующие StorageLocation
        user_warehouse_ids = []
        for wh in warehouses:
            loc = StorageLocation.objects.filter(source_type='склад', source_id=wh.id).first()
            if loc:
                user_warehouse_ids.append(loc.id)
            else:
                print(f"  - NOT found: {wh.name}")

        return user_warehouse_ids

    def clean_receipt_date(self):
        """Валидация даты поступления (только сегодня или прошедшие 7 дней, не будущая)"""
        receipt_date = self.cleaned_data.get('receipt_date')
        if receipt_date:
            now = timezone.now()
            # Устанавливаем границу 7 дней назад (начало дня)
            min_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

            if receipt_date > now:
                raise forms.ValidationError('Дата поступления не может быть в будущем')
            if receipt_date < min_date:
                raise forms.ValidationError(
                    'Можно указать дату не более 7 дней назад (начиная с {:%d.%m.%Y})'.format(min_date))
        return receipt_date

    def clean(self):
        """Валидация - хотя бы одно количество должно быть указано"""
        cleaned_data = super().clean()
        quantity_pieces = cleaned_data.get('quantity_pieces')
        quantity_meters = cleaned_data.get('quantity_meters')
        quantity_cubic = cleaned_data.get('quantity_cubic')

        if not quantity_pieces and not quantity_meters and not quantity_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество')

        return cleaned_data

    def save(self, commit=True, position=None, user=None):
        """Сохраняет остаток и создает поступление"""
        from Forest_apps.inventory.models import Receipt

        storage_location = self.cleaned_data['storage_location']
        material = self.cleaned_data['material']
        quantity_pieces = self.cleaned_data.get('quantity_pieces') or 0
        quantity_meters = self.cleaned_data.get('quantity_meters') or 0
        quantity_cubic = self.cleaned_data.get('quantity_cubic') or 0

        # Если редактируем существующее поступление
        if self.receipt_instance:
            if not self.receipt_instance.can_edit:
                raise ValueError('Поступление старше 5 дней, редактирование невозможно')

            old_storage_location = self.receipt_instance.storage_location
            old_material = self.receipt_instance.material
            old_pieces = self.receipt_instance.quantity_pieces or 0
            old_meters = self.receipt_instance.quantity_meters or 0
            old_cubic = self.receipt_instance.quantity_cubic or 0

            # Если меняется склад или материал - нужно корректно перенести остатки
            if old_storage_location != storage_location or old_material != material:
                # Сначала удаляем со старого склада
                try:
                    old_balance = MaterialBalance.objects.get(
                        storage_location=old_storage_location,
                        material=old_material
                    )
                except MaterialBalance.DoesNotExist:
                    raise ValueError(
                        f'Остаток материала {old_material.name} не найден на складе {old_storage_location.get_source_name()}')

                # Проверяем достаточно ли материала для удаления
                if old_pieces > 0 and old_balance.quantity_pieces < old_pieces:
                    raise ValueError(
                        f'Недостаточно материала на складе {old_storage_location.get_source_name()}. В наличии: {old_balance.quantity_pieces} шт, требуется удалить: {old_pieces} шт')
                if old_meters > 0 and (old_balance.quantity_meters or 0) < old_meters:
                    raise ValueError(
                        f'Недостаточно материала на складе {old_storage_location.get_source_name()}. В наличии: {old_balance.quantity_meters or 0} м.п., требуется удалить: {old_meters} м.п.')
                if old_cubic > 0 and (old_balance.quantity_cubic or 0) < old_cubic:
                    raise ValueError(
                        f'Недостаточно материала на складе {old_storage_location.get_source_name()}. В наличии: {old_balance.quantity_cubic or 0} м³, требуется удалить: {old_cubic} м³')

                # Удаляем со старого склада
                old_balance.quantity_pieces -= old_pieces
                old_balance.quantity_meters = (old_balance.quantity_meters or 0) - old_meters
                old_balance.quantity_cubic = (old_balance.quantity_cubic or 0) - old_cubic
                old_balance.save()

                # Добавляем на новый склад
                try:
                    new_balance = MaterialBalance.objects.get(
                        storage_location=storage_location,
                        material=material
                    )
                    new_balance.quantity_pieces += quantity_pieces
                    new_balance.quantity_meters = (new_balance.quantity_meters or 0) + quantity_meters
                    new_balance.quantity_cubic = (new_balance.quantity_cubic or 0) + quantity_cubic
                    new_balance.save()
                except MaterialBalance.DoesNotExist:
                    new_balance = MaterialBalance.objects.create(
                        storage_location=storage_location,
                        material=material,
                        quantity_pieces=quantity_pieces,
                        quantity_meters=quantity_meters,
                        quantity_cubic=quantity_cubic,
                        created_by=user,
                        created_by_position=position
                    )
            else:
                # Тот же склад - просто обновляем количество
                try:
                    balance = MaterialBalance.objects.get(
                        storage_location=storage_location,
                        material=material
                    )
                except MaterialBalance.DoesNotExist:
                    raise ValueError(
                        f'Остаток материала {material.name} не найден на складе {storage_location.get_source_name()}')

                diff_pieces = quantity_pieces - old_pieces
                diff_meters = quantity_meters - old_meters
                diff_cubic = quantity_cubic - old_cubic

                # Проверяем, достаточно ли материала для уменьшения
                if diff_pieces < 0 and balance.quantity_pieces + diff_pieces < 0:
                    raise ValueError(
                        f'Недостаточно материала на складе {storage_location.get_source_name()}. В наличии: {balance.quantity_pieces} шт')
                if diff_meters < 0 and (balance.quantity_meters or 0) + diff_meters < 0:
                    raise ValueError(
                        f'Недостаточно материала на складе {storage_location.get_source_name()}. В наличии: {balance.quantity_meters or 0} м.п.')
                if diff_cubic < 0 and (balance.quantity_cubic or 0) + diff_cubic < 0:
                    raise ValueError(
                        f'Недостаточно материала на складе {storage_location.get_source_name()}. В наличии: {balance.quantity_cubic or 0} м³')

                balance.quantity_pieces += diff_pieces
                balance.quantity_meters = (balance.quantity_meters or 0) + diff_meters
                balance.quantity_cubic = (balance.quantity_cubic or 0) + diff_cubic
                balance.save()

            # Обновляем поступление
            self.receipt_instance.receipt_date = self.cleaned_data['receipt_date']
            self.receipt_instance.storage_location = storage_location
            self.receipt_instance.material = material
            self.receipt_instance.source_location = self.cleaned_data.get('source_location')
            self.receipt_instance.price = self.cleaned_data.get('price')
            self.receipt_instance.quantity_pieces = quantity_pieces
            self.receipt_instance.quantity_meters = quantity_meters
            self.receipt_instance.quantity_cubic = quantity_cubic
            self.receipt_instance.save()

            return balance if 'balance' in locals() else new_balance

        # Создаем новое поступление
        receipt = Receipt.objects.create(
            receipt_date=self.cleaned_data['receipt_date'],
            material=material,
            storage_location=storage_location,
            source_location=self.cleaned_data.get('source_location'),
            quantity_pieces=quantity_pieces,
            quantity_meters=quantity_meters,
            quantity_cubic=quantity_cubic,
            price=self.cleaned_data.get('price'),
            created_by=user,
            created_by_position=position
        )

        # Обновляем или создаем остаток
        try:
            balance = MaterialBalance.objects.get(
                storage_location=storage_location,
                material=material
            )
            balance.quantity_pieces += quantity_pieces
            balance.quantity_meters = (balance.quantity_meters or 0) + quantity_meters
            balance.quantity_cubic = (balance.quantity_cubic or 0) + quantity_cubic
            balance.save()
        except MaterialBalance.DoesNotExist:
            balance = MaterialBalance.objects.create(
                storage_location=storage_location,
                material=material,
                quantity_pieces=quantity_pieces,
                quantity_meters=quantity_meters,
                quantity_cubic=quantity_cubic,
                created_by=user,
                created_by_position=position
            )

        return balance