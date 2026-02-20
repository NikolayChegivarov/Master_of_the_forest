from django import forms
from Forest_apps.core.models import Brigade


class BrigadeCreateForm(forms.ModelForm):
    """Форма создания бригады"""

    class Meta:
        model = Brigade
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название бригады',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название бригады'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных"""
        name = self.cleaned_data['name']

        # Проверяем, существует ли уже активная бригада с таким названием
        if Brigade.objects.filter(name__iexact=name, is_active=True).exists():
            raise forms.ValidationError('Бригада с таким названием уже существует')

        return name


class BrigadeEditForm(forms.ModelForm):
    """Форма редактирования бригады"""

    class Meta:
        model = Brigade
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название бригады',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название бригады'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность среди активных, исключая текущую"""
        name = self.cleaned_data['name']
        instance = self.instance

        # Проверяем, существует ли уже активная бригада с таким названием
        # Исключаем текущую бригаду из проверки
        if Brigade.objects.filter(name__iexact=name, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Бригада с таким названием уже существует')

        return name