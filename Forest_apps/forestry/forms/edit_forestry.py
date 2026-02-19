from django import forms
from Forest_apps.forestry.models import Forestry


class ForestryEditForm(forms.ModelForm):
    """Форма редактирования лесничества"""

    class Meta:
        model = Forestry
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название лесничества',
                'autofocus': True
            })
        }
        labels = {
            'name': 'Название лесничества'
        }

    def clean_name(self):
        """Валидация названия - проверка на уникальность"""
        name = self.cleaned_data['name']
        instance = self.instance

        # Проверяем, существует ли уже активное лесничество с таким названием
        # Исключаем текущее лесничество из проверки
        if Forestry.objects.filter(name__iexact=name, is_active=True).exclude(id=instance.id).exists():
            raise forms.ValidationError('Лесничество с таким названием уже существует')

        return name