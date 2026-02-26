from django import forms
from Forest_apps.inventory.models import MaterialMovement, StorageLocation
from Forest_apps.forestry.models import Material


class MaterialMovementCreateForm(forms.ModelForm):
    """Форма создания движения материалов"""

    class Meta:
        model = MaterialMovement
        fields = [
            'accounting_type',
            'from_location', 'to_location',
            'material', 'quantity_pieces', 'quantity_meters', 'quantity_cubic',
            'employee', 'vehicle', 'price'
        ]
        widgets = {
            'accounting_type': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'from_location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'to_location': forms.Select(attrs={
                'class': 'form-control'
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
            'vehicle': 'Транспорт',
            'price': 'Цена',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Устанавливаем queryset'ы
        self.fields['from_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['to_location'].queryset = StorageLocation.objects.all().order_by('source_type')
        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')

        from Forest_apps.employees.models import Employee
        from Forest_apps.core.models import Vehicle

        self.fields['employee'].queryset = Employee.objects.filter(
            position__name__icontains='водитель',
            is_active=True
        ).order_by('last_name', 'first_name')

        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('brand', 'model')

        # Делаем поля необязательными
        self.fields['to_location'].required = False
        self.fields['employee'].required = False
        self.fields['vehicle'].required = False
        self.fields['price'].required = False

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        accounting_type = cleaned_data.get('accounting_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')
        quantity_pieces = cleaned_data.get('quantity_pieces')
        quantity_meters = cleaned_data.get('quantity_meters')
        quantity_cubic = cleaned_data.get('quantity_cubic')
        price = cleaned_data.get('price')

        # Проверка наличия хотя бы одного количества
        if not quantity_pieces and not quantity_meters and not quantity_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество')

        # Проверки для разных типов движения
        if accounting_type == 'Перемещение':
            if not to_location:
                raise forms.ValidationError('Для перемещения необходимо указать получателя')
            if from_location.source_type in ['контрагент'] or to_location.source_type in ['контрагент']:
                raise forms.ValidationError('В перемещении не могут участвовать контрагенты')
            if price:
                raise forms.ValidationError('Для перемещения цена не указывается')

        elif accounting_type == 'Отправление':
            if not to_location:
                raise forms.ValidationError('Для отправления необходимо указать получателя')
            if from_location.source_type in ['контрагент'] or to_location.source_type in ['контрагент']:
                raise forms.ValidationError('В отправлении не могут участвовать контрагенты')
            if price:
                raise forms.ValidationError('Для отправления цена не указывается')

        elif accounting_type == 'Реализация':
            if not to_location:
                raise forms.ValidationError('Для реализации необходимо указать получателя')
            if to_location.source_type != 'контрагент':
                raise forms.ValidationError('Для реализации получателем должен быть контрагент')
            if not price:
                raise forms.ValidationError('Для реализации необходимо указать цену')

        elif accounting_type == 'Списание':
            if to_location:
                raise forms.ValidationError('Для списания не нужно указывать получателя')
            if from_location.source_type not in ['склад', 'автомобиль']:
                raise forms.ValidationError('Списание возможно только со склада или автомобиля')
            if price:
                raise forms.ValidationError('Для списания цена не указывается')

        # Проверка что отправитель и получатель разные
        if from_location and to_location and from_location.id == to_location.id:
            raise forms.ValidationError('Отправитель и получатель не могут совпадать')

        return cleaned_data


class MaterialMovementFilterForm(forms.Form):
    """Форма для фильтрации движений материалов"""

    accounting_type = forms.ChoiceField(
        label='Тип движения',
        required=False,
        choices=[('', 'Все типы')] + MaterialMovement.ACCOUNTING_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    date_from = forms.DateField(
        label='Дата с',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        label='Дата по',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control auto-submit',
            'type': 'date'
        })
    )

    from_location = forms.ModelChoiceField(
        label='Откуда',
        required=False,
        queryset=StorageLocation.objects.all().order_by('source_type'),
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    to_location = forms.ModelChoiceField(
        label='Куда',
        required=False,
        queryset=StorageLocation.objects.all().order_by('source_type'),
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    material = forms.ModelChoiceField(
        label='Материал',
        required=False,
        queryset=Material.objects.all().order_by('material_type', 'name'),
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    is_completed = forms.ChoiceField(
        label='Статус',
        required=False,
        choices=[
            ('', 'Все'),
            ('true', 'Выполнено'),
            ('false', 'Не выполнено')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )

    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по материалу или месту...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Queryset'ы уже установлены в определении полей, дополнительная настройка не требуется
        pass