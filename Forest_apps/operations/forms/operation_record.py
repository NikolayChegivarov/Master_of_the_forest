from django import forms
from Forest_apps.operations.models import OperationRecord
from Forest_apps.core.models import Warehouse
from Forest_apps.forestry.models import Material


class OperationRecordCreateForm(forms.ModelForm):
    """Форма создания записи операции"""

    class Meta:
        model = OperationRecord
        fields = ['operation_type', 'warehouse', 'material', 'quantity']
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
                'placeholder': 'Количество',
                'step': '0.001',
                'min': '0.001'
            }),
        }
        labels = {
            'operation_type': 'Тип операции',
            'warehouse': 'Склад',
            'material': 'Материал',
            'quantity': 'Количество',
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

    def _get_user_warehouse_ids(self):
        """Получает ID складов, принадлежащих пользователю"""
        if not self.user or not self.user.is_authenticated:
            return []

        from Forest_apps.core.models import Warehouse

        # Склады, созданные пользователем
        return Warehouse.objects.filter(created_by=self.user).values_list('id', flat=True)


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