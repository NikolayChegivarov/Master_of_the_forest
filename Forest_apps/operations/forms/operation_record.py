# Forest_apps/operations/forms/operation_record.py
from django import forms
from Forest_apps.operations.models import OperationRecord
from Forest_apps.core.models import Warehouse
from Forest_apps.forestry.models import Material


class OperationRecordCreateForm(forms.ModelForm):
    """Форма создания записи операции"""

    class Meta:
        model = OperationRecord
        fields = ['operation_type', 'warehouse', 'material', 'quantity', 'square_meters', 'cubic_meters']
        widgets = {
            'operation_type': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в штуках',
                'step': '0.001',
                'min': '0.001'
            }),
            'square_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Площадь в м²',
                'step': '0.001',
                'min': '0.001'
            }),
            'cubic_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Объем в м³',
                'step': '0.001',
                'min': '0.001'
            }),
        }
        labels = {
            'operation_type': 'Тип операции',
            'warehouse': 'Склад',
            'material': 'Материал',
            'quantity': 'Количество (шт)',
            'square_meters': 'Площадь (м²)',
            'cubic_meters': 'Объем (м³)',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Только активные типы операций
        from Forest_apps.operations.models import OperationType
        self.fields['operation_type'].queryset = OperationType.objects.filter(
            is_active=True
        ).order_by('name')

        # Только склады, принадлежащие пользователю
        user_warehouse_ids = self._get_user_warehouse_ids()
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            id__in=user_warehouse_ids
        ).order_by('name')

        # Все материалы, сортировка по типу и названию
        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')

        # Делаем поля площади и объема необязательными
        self.fields['square_meters'].required = False
        self.fields['cubic_meters'].required = False

    def _get_user_warehouse_ids(self):
        """Получает ID складов, принадлежащих пользователю"""
        if not self.user or not self.user.is_authenticated:
            return []

        from Forest_apps.core.models import Warehouse

        # Склады, созданные пользователем
        return Warehouse.objects.filter(created_by=self.user).values_list('id', flat=True)

    def clean(self):
        cleaned_data = super().clean()
        square_meters = cleaned_data.get('square_meters')
        cubic_meters = cleaned_data.get('cubic_meters')

        # Проверка, что хотя бы одно из полей (количество, площадь или объем) заполнено
        if not square_meters and not cubic_meters:
            # Если не заполнены ни площадь, ни объем, то количество обязательно
            quantity = cleaned_data.get('quantity')
            if not quantity:
                raise forms.ValidationError(
                    'Необходимо указать хотя бы одно из значений: количество, площадь или объем'
                )

        return cleaned_data


class OperationRecordFilterForm(forms.Form):
    """Форма фильтрации записей операций"""

    operation_type = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Тип операции',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    warehouse = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Склад',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    material = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Материал',
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

    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по материалу...'
        })
    )

    has_measurements = forms.ChoiceField(
        choices=[
            ('', 'Все записи'),
            ('with_square', 'Только с площадью'),
            ('with_cubic', 'Только с объемом'),
            ('with_both', 'С площадью и объемом'),
        ],
        required=False,
        label='Измерения',
        widget=forms.Select(attrs={'class': 'form-control auto-submit'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        from Forest_apps.operations.models import OperationType
        from Forest_apps.core.models import Warehouse
        from Forest_apps.forestry.models import Material

        self.fields['operation_type'].queryset = OperationType.objects.filter(
            is_active=True
        ).order_by('name')

        # Для фильтра складов показываем только склады пользователя
        if user and user.is_authenticated:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                created_by=user
            ).order_by('name')
        else:
            self.fields['warehouse'].queryset = Warehouse.objects.all().order_by('name')

        self.fields['material'].queryset = Material.objects.all().order_by('material_type', 'name')