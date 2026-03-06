from django import forms
from django.utils import timezone
from Forest_apps.inventory.models import MaterialMovement, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.employees.models import Employee
from Forest_apps.core.models import Vehicle
from decimal import Decimal


class MaterialMovementFilterForm(forms.Form):
    """Форма фильтрации движений материалов"""
    accounting_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + MaterialMovement.ACCOUNTING_TYPE_CHOICES,
        required=False,
        label='Тип движения',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    date_from = forms.DateField(
        required=False,
        label='Дата с',
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        required=False,
        label='Дата по',
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )

    from_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.all().order_by('source_type'),
        required=False,
        label='Откуда',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    to_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.all().order_by('source_type'),
        required=False,
        label='Куда',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material = forms.ModelChoiceField(
        queryset=Material.objects.all().order_by('name'),
        required=False,
        label='Материал',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    is_completed = forms.ChoiceField(
        choices=[
            ('', 'Все'),
            ('true', 'Выполнено'),
            ('false', 'Не выполнено')
        ],
        required=False,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по материалу...'
        })
    )


class MaterialMovementCreateForm(forms.ModelForm):
    """Форма создания движения материалов"""

    class Meta:
        model = MaterialMovement
        fields = [
            'accounting_type', 'from_location', 'to_location', 'material',
            'quantity_pieces', 'quantity_meters', 'quantity_cubic',
            'employee', 'vehicle', 'price'
        ]
        widgets = {
            'accounting_type': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True,
                'id': 'id_accounting_type'
            }),
            'from_location': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_from_location'
            }),
            'to_location': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_to_location'
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
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'vehicle': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Цена за единицу',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'accounting_type': 'Тип движения',
            'from_location': 'Откуда',
            'to_location': 'Куда',
            'material': 'Материал',
            'quantity_pieces': 'Штуки',
            'quantity_meters': 'Погонные метры',
            'quantity_cubic': 'Кубические метры',
            'employee': 'Водитель',
            'vehicle': 'Транспортное средство',
            'price': 'Цена',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Получаем ID мест хранения, принадлежащих пользователю
        self.user_location_ids = self._get_user_location_ids()

        # Получаем ID мест хранения, НЕ принадлежащих пользователю
        self.foreign_location_ids = self._get_foreign_location_ids()

        # Получаем ID контрагентов
        self.counterparty_ids = self._get_counterparty_ids()

        # Получаем ID бригад и автомобилей (для списания)
        self.brigade_and_vehicle_ids = self._get_brigade_and_vehicle_ids()

        # Устанавливаем начальные queryset'ы
        self.fields['from_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['to_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')
        self.fields['employee'].queryset = Employee.objects.filter(
            position__name__icontains='водитель'
        ).order_by('last_name', 'first_name')
        self.fields['vehicle'].queryset = Vehicle.objects.all().order_by('brand', 'model')

        # Если это редактирование, применяем фильтры в соответствии с типом движения
        if self.instance and self.instance.pk:
            self._apply_filters_for_type(self.instance.accounting_type)

    def _get_user_location_ids(self):
        """Получает ID мест хранения, принадлежащих пользователю"""
        if not self.user or not self.user.is_authenticated:
            return []

        from Forest_apps.core.models import Warehouse, Brigade, Vehicle
        from Forest_apps.inventory.models import StorageLocation

        user_location_ids = []

        # Склады, созданные пользователем
        warehouses = Warehouse.objects.filter(created_by=self.user)
        for wh in warehouses:
            try:
                location = StorageLocation.objects.get(source_type='склад', source_id=wh.id)
                user_location_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

        # Бригады, созданные пользователем
        brigades = Brigade.objects.filter(created_by=self.user)
        for br in brigades:
            try:
                location = StorageLocation.objects.get(source_type='бригады', source_id=br.id)
                user_location_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

        # Транспорт, созданный пользователем
        vehicles = Vehicle.objects.filter(created_by=self.user)
        for vh in vehicles:
            try:
                location = StorageLocation.objects.get(source_type='автомобиль', source_id=vh.id)
                user_location_ids.append(location.id)
            except StorageLocation.DoesNotExist:
                pass

        return user_location_ids

    def _get_foreign_location_ids(self):
        """Получает ID мест хранения, НЕ принадлежащих пользователю"""
        all_locations = StorageLocation.objects.all().values_list('id', flat=True)
        return [loc_id for loc_id in all_locations if loc_id not in self.user_location_ids]

    def _get_counterparty_ids(self):
        """Получает ID мест хранения типа 'контрагент'"""
        from Forest_apps.inventory.models import StorageLocation
        return list(StorageLocation.objects.filter(source_type='контрагент').values_list('id', flat=True))

    def _get_brigade_and_vehicle_ids(self):
        """Получает ID мест хранения типа 'бригады' и 'автомобиль'"""
        from Forest_apps.inventory.models import StorageLocation
        return list(StorageLocation.objects.filter(
            source_type__in=['бригады', 'автомобиль']
        ).values_list('id', flat=True))

    def _apply_filters_for_type(self, accounting_type):
        """Применяет фильтры к полям в зависимости от типа движения"""

        if accounting_type == 'Перемещение':
            # Перемещение: откуда и куда - только свои места
            self.fields['from_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids
            ).order_by('source_type')
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids
            ).order_by('source_type')

        elif accounting_type == 'Отправление':
            # Отправление: откуда - свои, куда - чужие (но не контрагенты)
            self.fields['from_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids
            ).order_by('source_type')
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                id__in=self.foreign_location_ids
            ).exclude(
                source_type='контрагент'
            ).order_by('source_type')

        elif accounting_type == 'Реализация':
            # Реализация: откуда - все, куда - только контрагенты
            self.fields['from_location'].queryset = StorageLocation.objects.all().order_by('source_type')
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                source_type='контрагент'
            ).order_by('source_type')

        elif accounting_type == 'Списание':
            # Списание: откуда - свои, куда - бригады и автомобили
            self.fields['from_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids
            ).order_by('source_type')
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                id__in=self.brigade_and_vehicle_ids
            ).order_by('source_type')

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        accounting_type = cleaned_data.get('accounting_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')
        price = cleaned_data.get('price')

        quantity_pieces = cleaned_data.get('quantity_pieces')
        quantity_meters = cleaned_data.get('quantity_meters')
        quantity_cubic = cleaned_data.get('quantity_cubic')

        # Проверка - хотя бы одно количество должно быть указано
        if not quantity_pieces and not quantity_meters and not quantity_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество')

        # Валидация в зависимости от типа движения
        if accounting_type == 'Перемещение':
            if not from_location or not to_location:
                raise forms.ValidationError('Для перемещения необходимо указать отправителя и получателя')

            # Проверка, что оба места - свои
            if from_location and from_location.id not in self.user_location_ids:
                raise forms.ValidationError('Можно перемещать только со своих мест хранения')
            if to_location and to_location.id not in self.user_location_ids:
                raise forms.ValidationError('Можно перемещать только на свои места хранения')

            # Проверка, что это не контрагенты
            if from_location and from_location.source_type == 'контрагент':
                raise forms.ValidationError('Контрагенты не могут участвовать в перемещении')
            if to_location and to_location.source_type == 'контрагент':
                raise forms.ValidationError('Контрагенты не могут участвовать в перемещении')

        elif accounting_type == 'Отправление':
            if not from_location or not to_location:
                raise forms.ValidationError('Для отправления необходимо указать отправителя и получателя')

            # Проверка, что отправитель - свой
            if from_location and from_location.id not in self.user_location_ids:
                raise forms.ValidationError('Отправлять можно только со своих мест хранения')

            # Проверка, что получатель - чужой (и не контрагент)
            if to_location and to_location.id in self.user_location_ids:
                raise forms.ValidationError('Нельзя отправлять на свои места хранения')
            if to_location and to_location.source_type == 'контрагент':
                raise forms.ValidationError('Контрагенты не могут участвовать в отправлении')

        elif accounting_type == 'Реализация':
            if not to_location:
                raise forms.ValidationError('Для реализации необходимо указать получателя')

            # Проверка, что получатель - контрагент
            if to_location and to_location.source_type != 'контрагент':
                raise forms.ValidationError('Получателем при реализации должен быть контрагент')

            # Проверка цены
            if not price:
                raise forms.ValidationError('Для реализации необходимо указать цену')
            if price <= 0:
                raise forms.ValidationError('Цена должна быть положительным числом')

        elif accounting_type == 'Списание':
            if not from_location:
                raise forms.ValidationError('Для списания необходимо указать отправителя')

            # Проверка, что отправитель - свой
            if from_location and from_location.id not in self.user_location_ids:
                raise forms.ValidationError('Списывать можно только со своих мест хранения')

            # Проверка, что отправитель - склад или автомобиль
            if from_location and from_location.source_type not in ['склад', 'автомобиль']:
                raise forms.ValidationError('Списание возможно только со склада или автомобиля')

        return cleaned_data