# ФОРМЫ КОНВЕРТАЦИЯ
from django import forms
from django.utils import timezone
from Forest_apps.inventory.models import Conversion #, StorageLocation
from Forest_apps.forestry.models import Material
from Forest_apps.inventory.services import StorageLocationService


class ConversionCreateForm(forms.ModelForm):
    """Форма создания конвертации древесины"""

    conversion_date = forms.DateTimeField(
        label='Дата конвертации',
        required=False,
        initial=timezone.now,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = Conversion
        fields = [
            'storage_location', 'conversion_date',
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
            'conversion_date': 'Дата конвертации',
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
        self.position_name = kwargs.pop('position_name', None)
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Если это редактирование, подставляем дату
        if self.instance and self.instance.pk:
            self.initial['conversion_date'] = self.instance.conversion_date.strftime('%Y-%m-%dT%H:%M')
        else:
            self.initial['conversion_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

        # Если это редактирование, полностью убираем поле storage_location из формы
        if self.instance and self.instance.pk:
            self.fields.pop('storage_location')
        else:
            # Только при создании - получаем склады через сервис по должности
            user_warehouses = StorageLocationService.get_user_warehouses_by_position_name(self.position_name)
            self.fields['storage_location'].queryset = user_warehouses

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

    def save(self, commit=True, position=None, user=None):
        """Сохраняет конвертацию"""
        conversion = super().save(commit=False)

        # Устанавливаем дату из формы
        if self.cleaned_data.get('conversion_date'):
            conversion.conversion_date = self.cleaned_data['conversion_date']
        else:
            conversion.conversion_date = timezone.now()

        # При редактировании storage_location уже есть в instance
        if not self.instance or not self.instance.pk:
            # При создании - передаем склад из формы
            conversion.storage_location = self.cleaned_data.get('storage_location')

        if commit:
            conversion.save()

        return conversion