from django import forms
from Forest_apps.core.models import Position


class PositionCreateForm(forms.ModelForm):
    """Форма создания должности"""

    class Meta:
        model = Position
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название должности',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название должности'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных"""
        name = self.cleaned_data['name']

        # Проверяем, существует ли уже активная должность с таким названием
        if Position.objects.filter(name__iexact=name, is_active=True).exists():
            raise forms.ValidationError('Должность с таким названием уже существует')

        return name


class PositionEditForm(forms.ModelForm):
    """Форма редактирования должности"""

    class Meta:
        model = Position
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название должности',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название должности'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных, исключая текущую"""
        name = self.cleaned_data['name']
        instance = self.instance

        # Проверяем, существует ли уже активная должность с таким названием
        # Исключаем текущую должность из проверки
        if Position.objects.filter(name__iexact=name, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Должность с таким названием уже существует')

        return name