
from django import forms
from Forest_apps.inventory.models import StorageLocation


class StorageLocationTypeForm(forms.Form):
    """Форма для фильтрации по типу (автоматическая)"""

    source_type = forms.ChoiceField(
        label='Тип',
        required=False,
        choices=[('', 'Все типы')] + StorageLocation.SOURCE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit();'
        })
    )


class StorageLocationSearchForm(forms.Form):
    """Форма для поиска по названию (с кнопкой)"""

    search = forms.CharField(
        label='Поиск по названию',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название для поиска...'
        })
    )