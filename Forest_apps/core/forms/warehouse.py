from django import forms
from Forest_apps.core.models import Warehouse


class WarehouseCreateForm(forms.ModelForm):
    """Форма создания склада"""

    class Meta:
        model = Warehouse
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название склада',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название склада'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных"""
        name = self.cleaned_data['name']

        # Проверяем, существует ли уже активный склад с таким названием
        if Warehouse.objects.filter(name__iexact=name, is_active=True).exists():
            raise forms.ValidationError('Склад с таким названием уже существует')

        return name


class WarehouseEditForm(forms.ModelForm):
    """Форма редактирования склада"""

    class Meta:
        model = Warehouse
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название склада',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название склада'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных, исключая текущий"""
        name = self.cleaned_data['name']
        instance = self.instance

        # Проверяем, существует ли уже активный склад с таким названием
        # Исключаем текущий склад из проверки
        if Warehouse.objects.filter(name__iexact=name, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Склад с таким названием уже существует')

        return name