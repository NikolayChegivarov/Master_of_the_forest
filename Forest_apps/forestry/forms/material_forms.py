from django import forms
from Forest_apps.forestry.models import Material


class MaterialCreateForm(forms.ModelForm):
    """Форма создания материала"""

    class Meta:
        model = Material
        fields = ['material_type', 'name']
        widgets = {
            'material_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование материала',
                'autofocus': True
            }),
        }
        labels = {
            'material_type': 'Тип материала',
            'name': 'Наименование',
        }

    def clean(self):
        """Валидация уникальности материала"""
        cleaned_data = super().clean()
        material_type = cleaned_data.get('material_type')
        name = cleaned_data.get('name')

        if material_type and name:
            # Проверяем, существует ли уже материал с таким типом и названием
            if Material.objects.filter(
                    material_type=material_type,
                    name__iexact=name
            ).exists():
                raise forms.ValidationError(
                    f'Материал с типом "{material_type}" и названием "{name}" уже существует'
                )

        return cleaned_data


class MaterialEditForm(forms.ModelForm):
    """Форма редактирования материала"""

    class Meta:
        model = Material
        fields = ['material_type', 'name', 'is_active']
        widgets = {
            'material_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование материала'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'material_type': 'Тип материала',
            'name': 'Наименование',
            'is_active': 'Активен',
        }

    def clean(self):
        """Валидация уникальности материала при редактировании"""
        cleaned_data = super().clean()
        material_type = cleaned_data.get('material_type')
        name = cleaned_data.get('name')
        instance = self.instance

        if material_type and name:
            # Проверяем, существует ли уже материал с таким типом и названием
            # Исключаем текущий материал из проверки
            if Material.objects.filter(
                    material_type=material_type,
                    name__iexact=name
            ).exclude(id=instance.id).exists():
                raise forms.ValidationError(
                    f'Материал с типом "{material_type}" и названием "{name}" уже существует'
                )

        return cleaned_data