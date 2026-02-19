from django import forms
from Forest_apps.forestry.models import CuttingArea, Forestry


class CuttingAreaCreateForm(forms.ModelForm):
    """Форма создания лесосеки"""

    forestry = forms.ModelChoiceField(
        queryset=Forestry.objects.filter(is_active=True),
        empty_label="--- Выберите лесничество ---",
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Лесничество'
    )

    class Meta:
        model = CuttingArea
        fields = ['forestry', 'quarter_number', 'division_number', 'area_hectares']
        widgets = {
            'quarter_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите номер квартала'
            }),
            'division_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите номер выдела'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите площадь в гектарах',
                'step': '0.01',
                'min': '0'
            }),
        }
        labels = {
            'quarter_number': 'Номер квартала',
            'division_number': 'Номер выдела',
            'area_hectares': 'Площадь выдела (Га)',
        }

    def clean(self):
        """Валидация уникальности лесосеки"""
        cleaned_data = super().clean()
        forestry = cleaned_data.get('forestry')
        quarter_number = cleaned_data.get('quarter_number')
        division_number = cleaned_data.get('division_number')

        if forestry and quarter_number and division_number:
            # Проверяем, существует ли уже активная лесосека с таким адресом
            if CuttingArea.objects.filter(
                    forestry=forestry,
                    quarter_number=quarter_number,
                    division_number=division_number,
                    is_active=True
            ).exists():
                raise forms.ValidationError(
                    f'Лесосека с адресом "{forestry.name}, кв.{quarter_number}, выд.{division_number}" уже существует'
                )

        return cleaned_data


class CuttingAreaEditForm(forms.ModelForm):
    """Форма редактирования лесосеки"""

    forestry = forms.ModelChoiceField(
        queryset=Forestry.objects.filter(is_active=True),
        empty_label="--- Выберите лесничество ---",
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Лесничество'
    )

    class Meta:
        model = CuttingArea
        fields = ['forestry', 'quarter_number', 'division_number', 'area_hectares', 'is_active']
        widgets = {
            'quarter_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите номер квартала'
            }),
            'division_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите номер выдела'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите площадь в гектарах',
                'step': '0.01',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'quarter_number': 'Номер квартала',
            'division_number': 'Номер выдела',
            'area_hectares': 'Площадь выдела (Га)',
            'is_active': 'Активна',
        }

    def clean(self):
        """Валидация уникальности лесосеки при редактировании"""
        cleaned_data = super().clean()
        forestry = cleaned_data.get('forestry')
        quarter_number = cleaned_data.get('quarter_number')
        division_number = cleaned_data.get('division_number')
        instance = self.instance

        if forestry and quarter_number and division_number:
            # Проверяем, существует ли уже активная лесосека с таким адресом
            # Исключаем текущую лесосеку из проверки
            if CuttingArea.objects.filter(
                    forestry=forestry,
                    quarter_number=quarter_number,
                    division_number=division_number,
                    is_active=True
            ).exclude(id=instance.id).exists():
                raise forms.ValidationError(
                    f'Лесосека с адресом "{forestry.name}, кв.{quarter_number}, выд.{division_number}" уже существует'
                )

        return cleaned_data