# ФОРМЫ ДВИЖЕНИЕ МАТЕРИАЛОВ
from django import forms
from django.utils import timezone
from Forest_apps.inventory.models import MaterialMovement, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.employees.models import Employee
from Forest_apps.core.models import Vehicle, Position
from decimal import Decimal
from Forest_apps.inventory.services import StorageLocationService


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
        self.position_name = kwargs.pop('position_name', None)  # Получаем должность
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # ОПРЕДЕЛЯЕМ ДОЛЖНОСТЬ ПОЛЬЗОВАТЕЛЯ
        is_supervisor = (self.position_name and self.position_name.lower() == 'руководитель')

        # ФОРМИРУЕМ СПИСОК ТИПОВ ДВИЖЕНИЯ В ЗАВИСИМОСТИ ОТ ДОЛЖНОСТИ
        all_choices = MaterialMovement.ACCOUNTING_TYPE_CHOICES

        if is_supervisor:
            # Для руководителя - только Реализация
            filtered_choices = [choice for choice in all_choices if choice[0] == 'Реализация']
        else:
            # Для всех остальных - все кроме Реализации
            filtered_choices = [choice for choice in all_choices if choice[0] != 'Реализация']

        # Применяем отфильтрованные choices к полю
        self.fields['accounting_type'].choices = filtered_choices

        # Если есть только один вариант и он не выбран, устанавливаем его по умолчанию
        if len(filtered_choices) == 1 and not self.initial.get('accounting_type') and not self.instance:
            self.initial['accounting_type'] = filtered_choices[0][0]

        # ПОЛУЧАЕМ МЕСТА ХРАНЕНИЯ ЧЕРЕЗ СЕРВИС
        # Получаем ID мест хранения, принадлежащих пользователю
        user_locations = StorageLocationService.get_user_storage_locations_by_position_name(
            self.position_name
        )
        self.user_location_ids = list(user_locations.values_list('id', flat=True))

        # Получаем ID мест хранения, НЕ принадлежащих пользователю
        all_location_ids = list(StorageLocation.objects.all().values_list('id', flat=True))
        self.foreign_location_ids = [loc_id for loc_id in all_location_ids if loc_id not in self.user_location_ids]

        # Получаем ID контрагентов
        self.counterparty_ids = list(StorageLocation.objects.filter(
            source_type='контрагент'
        ).values_list('id', flat=True))

        # Получаем ID бригад и автомобилей (для списания)
        self.brigade_and_vehicle_ids = list(StorageLocation.objects.filter(
            source_type__in=['бригады', 'автомобиль']
        ).values_list('id', flat=True))

        # Устанавливаем начальные queryset'ы
        self.fields['from_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['to_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')

        # Фильтруем сотрудников только с должностью "водитель"
        driver_position = Position.objects.filter(name__iexact='водитель').first()
        if driver_position:
            self.fields['employee'].queryset = Employee.objects.filter(
                position=driver_position,
                is_active=True
            ).order_by('last_name', 'first_name')
        else:
            self.fields['employee'].queryset = Employee.objects.none()

        self.fields['vehicle'].queryset = Vehicle.objects.all().order_by('brand', 'model')

        # Если это редактирование, применяем фильтры в соответствии с типом движения
        if self.instance and self.instance.pk:
            self._apply_filters_for_type(self.instance.accounting_type)

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
            # Реализация: откуда - только склады (все, не только свои)
            self.fields['from_location'].queryset = StorageLocation.objects.filter(
                source_type='склад'
            ).order_by('source_type')
            # Куда - только контрагенты
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                source_type='контрагент'
            ).order_by('source_type')

        elif accounting_type == 'Списание':
            # Списание: откуда - только свои склады
            self.fields['from_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids,
                source_type='склад'
            ).order_by('source_type')

            # Куда - ВСЕ свои места хранения кроме контрагентов (склады, бригады, автомобили)
            self.fields['to_location'].queryset = StorageLocation.objects.filter(
                id__in=self.user_location_ids
            ).exclude(
                source_type='контрагент'
            ).order_by('source_type')

            # Материалы - только ГСМ и запчасти
            self.fields['material'].queryset = Material.objects.filter(
                material_type__in=['ГСМ', 'запчасти']
            ).order_by('material_type', 'name')

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        accounting_type = cleaned_data.get('accounting_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')
        price = cleaned_data.get('price')
        material = cleaned_data.get('material')

        quantity_pieces = cleaned_data.get('quantity_pieces') or 0
        quantity_meters = cleaned_data.get('quantity_meters') or 0
        quantity_cubic = cleaned_data.get('quantity_cubic') or 0

        # Проверка - хотя бы одно количество должно быть указано
        if not quantity_pieces and not quantity_meters and not quantity_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество')

        # ========== ПРОВЕРКА ОСТАТКОВ (для всех типов, где списывается материал) ==========
        if accounting_type in ['Перемещение', 'Отправление', 'Реализация', 'Списание']:
            if from_location and material:
                from Forest_apps.inventory.models import MaterialBalance

                try:
                    balance = MaterialBalance.objects.get(
                        storage_location=from_location,
                        material=material
                    )

                    if quantity_pieces > 0 and (balance.quantity_pieces or 0) < quantity_pieces:
                        raise forms.ValidationError(
                            f'Недостаточно материала "{material.name}" на складе "{from_location.get_source_name()}". '
                            f'В наличии: {balance.quantity_pieces or 0} шт, требуется: {quantity_pieces} шт'
                        )

                    if quantity_meters > 0 and (balance.quantity_meters or 0) < quantity_meters:
                        raise forms.ValidationError(
                            f'Недостаточно материала "{material.name}" на складе "{from_location.get_source_name()}". '
                            f'В наличии: {balance.quantity_meters or 0} м.п., требуется: {quantity_meters} м.п.'
                        )

                    if quantity_cubic > 0 and (balance.quantity_cubic or 0) < quantity_cubic:
                        raise forms.ValidationError(
                            f'Недостаточно материала "{material.name}" на складе "{from_location.get_source_name()}". '
                            f'В наличии: {balance.quantity_cubic or 0} м³, требуется: {quantity_cubic} м³'
                        )

                except MaterialBalance.DoesNotExist:
                    raise forms.ValidationError(
                        f'Материал "{material.name}" отсутствует на складе "{from_location.get_source_name()}"'
                    )

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
            if not from_location:
                raise forms.ValidationError('Для реализации необходимо указать отправителя')
            if not to_location:
                raise forms.ValidationError('Для реализации необходимо указать получателя')

            # Проверка, что отправитель - склад
            if from_location and from_location.source_type != 'склад':
                raise forms.ValidationError('Отправителем при реализации может быть только склад')

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
            if not to_location:
                raise forms.ValidationError('Для списания необходимо указать получателя')

            # Проверка, что отправитель - только склад (свой)
            if from_location and from_location.id not in self.user_location_ids:
                raise forms.ValidationError('Списывать можно только со своих мест хранения')
            if from_location and from_location.source_type != 'склад':
                raise forms.ValidationError('Списание возможно только со склада')

            # Проверка, что получатель - свое место хранения (кроме контрагентов)
            if to_location and to_location.id not in self.user_location_ids:
                raise forms.ValidationError('Можно списывать только на свои места хранения')
            if to_location and to_location.source_type == 'контрагент':
                raise forms.ValidationError('Нельзя списывать на контрагентов')

            # Проверка типа материала
            if material and material.material_type not in ['ГСМ', 'запчасти']:
                raise forms.ValidationError('Списание возможно только для материалов типа ГСМ или запчасти')

        return cleaned_data


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