from django import forms
from Forest_apps.core.models import Vehicle


class VehicleCreateForm(forms.ModelForm):
    """Форма создания транспортного средства"""

    class Meta:
        model = Vehicle
        fields = ['brand', 'model', 'license_plate']
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите марку',
                'autofocus': True
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите модель'
            }),
            'license_plate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите гос номер (например: А123ВС77)'
            }),
        }
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'license_plate': 'Гос номер',
        }

    def clean_license_plate(self):
        """Валидация гос номера - проверка на уникальность"""
        license_plate = self.cleaned_data['license_plate'].upper()

        # Проверяем, существует ли уже активный транспорт с таким гос номером
        if Vehicle.objects.filter(license_plate__iexact=license_plate, is_active=True).exists():
            raise forms.ValidationError('Транспортное средство с таким гос номером уже существует')

        return license_plate


class VehicleEditForm(forms.ModelForm):
    """Форма редактирования транспортного средства"""

    class Meta:
        model = Vehicle
        fields = ['brand', 'model', 'license_plate']
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите марку',
                'autofocus': True
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите модель'
            }),
            'license_plate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите гос номер'
            }),
        }
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'license_plate': 'Гос номер',
        }

    def clean_license_plate(self):
        """Валидация гос номера - проверка на уникальность среди активных, исключая текущий"""
        license_plate = self.cleaned_data['license_plate'].upper()
        instance = self.instance

        # Проверяем, существует ли уже активный транспорт с таким гос номером
        # Исключаем текущее ТС из проверки
        if Vehicle.objects.filter(license_plate__iexact=license_plate, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Транспортное средство с таким гос номером уже существует')

        return license_plate