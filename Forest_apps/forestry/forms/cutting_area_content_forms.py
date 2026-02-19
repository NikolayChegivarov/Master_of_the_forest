from django import forms
from Forest_apps.forestry.models import CuttingAreaContent, Material, CuttingArea


class AddMaterialToCuttingAreaForm(forms.Form):
    """Форма для добавления материала в лесосеку"""

    material = forms.ModelChoiceField(
        queryset=Material.objects.all().order_by('material_type', 'name'),
        empty_label="--- Выберите материал ---",
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Материал'
    )

    quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите количество',
            'step': '0.001'
        }),
        label='Количество'
    )

    def __init__(self, cutting_area=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cutting_area = cutting_area

    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        quantity = cleaned_data.get('quantity')

        if material and quantity and self.cutting_area:
            # Проверяем, не превышает ли количество разумные пределы (опционально)
            if quantity <= 0:
                raise forms.ValidationError('Количество должно быть больше 0')

            # Можно добавить другие проверки, например, максимальное количество
            # if quantity > 10000:
            #     raise forms.ValidationError('Слишком большое количество')

        return cleaned_data


class UpdateMaterialQuantityForm(forms.Form):
    """Форма для обновления количества материала в лесосеке"""

    quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новое количество',
            'step': '0.001'
        }),
        label='Количество'
    )

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError('Количество должно быть больше 0')
        return quantity