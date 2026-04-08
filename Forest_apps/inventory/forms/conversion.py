# ФОРМЫ КОНВЕРТАЦИЯ
from django import forms
from Forest_apps.inventory.models import Conversion, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.inventory.services import StorageLocationService


class ConversionCreateForm(forms.ModelForm):
    """Форма создания конвертации древесины"""

    class Meta:
        model = Conversion
        fields = [
            'storage_location',
            'source_material', 'source_quantity_pieces', 'source_quantity_meters', 'source_quantity_cubic',
            'target_material', 'target_quantity_pieces', 'target_quantity_meters', 'target_quantity_cubic'
        ]
        widgets = {
            'storage_location': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True
            }),
            'source_material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'source_quantity_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в штуках',
                'step': '0.001',
                'min': '0'
            }),
            'source_quantity_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в погонных метрах',
                'step': '0.001',
                'min': '0'
            }),
            'source_quantity_cubic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в кубических метрах',
                'step': '0.001',
                'min': '0'
            }),
            'target_material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_quantity_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в штуках',
                'step': '0.001',
                'min': '0'
            }),
            'target_quantity_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в погонных метрах',
                'step': '0.001',
                'min': '0'
            }),
            'target_quantity_cubic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество в кубических метрах',
                'step': '0.001',
                'min': '0'
            }),
        }
        labels = {
            'storage_location': 'Склад',
            'source_material': 'Исходный материал (что списываем)',
            'source_quantity_pieces': 'Штуки',
            'source_quantity_meters': 'Погонные метры',
            'source_quantity_cubic': 'Кубические метры',
            'target_material': 'Целевой материал (что создаем)',
            'target_quantity_pieces': 'Штуки',
            'target_quantity_meters': 'Погонные метры',
            'target_quantity_cubic': 'Кубические метры',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.position_name = kwargs.pop('position_name', None)  # Добавляем должность
        super().__init__(*args, **kwargs)

        # Получаем склады через сервис
        user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(
            self.position_name
        )

        # Только склады, принадлежащие пользователю
        self.fields['storage_location'].queryset = user_warehouses.filter(source_type='склад')

        # Только материалы типа "древесина"
        self.fields['source_material'].queryset = Material.objects.filter(
            material_type='древесина'
        ).order_by('name')

        self.fields['target_material'].queryset = Material.objects.filter(
            material_type='древесина'
        ).order_by('name')

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()

        source_pieces = cleaned_data.get('source_quantity_pieces')
        source_meters = cleaned_data.get('source_quantity_meters')
        source_cubic = cleaned_data.get('source_quantity_cubic')

        target_pieces = cleaned_data.get('target_quantity_pieces')
        target_meters = cleaned_data.get('target_quantity_meters')
        target_cubic = cleaned_data.get('target_quantity_cubic')

        source_material = cleaned_data.get('source_material')
        target_material = cleaned_data.get('target_material')

        # Проверка, что указано хотя бы одно количество для исходного материала
        if not source_pieces and not source_meters and not source_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество для списания')

        # Проверка, что указано хотя бы одно количество для целевого материала
        if not target_pieces and not target_meters and not target_cubic:
            raise forms.ValidationError('Необходимо указать хотя бы одно количество для создания')

        # Проверка, что исходный и целевой материалы разные
        if source_material and target_material and source_material == target_material:
            raise forms.ValidationError('Исходный и целевой материалы должны быть разными')

        return cleaned_data