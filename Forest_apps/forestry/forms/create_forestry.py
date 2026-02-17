from django import forms
from Forest_apps.forestry.models import Forestry



class ForestryCreateForm(forms.ModelForm):
    """Форма создания лесничества"""

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

        # Проверяем, существует ли уже активное лесничество с таким названием
        if Forestry.objects.filter(name__iexact=name, is_active=True).exists():
            raise forms.ValidationError('Лесничество с таким названием уже существует')

        return name