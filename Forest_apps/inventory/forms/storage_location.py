from django import forms
from Forest_apps.inventory.models import StorageLocation


class StorageLocationFilterForm(forms.Form):
    """Форма для фильтрации мест хранения"""

    source_type = forms.ChoiceField(
        label='Тип',
        required=False,
        choices=[('', 'Все типы')] + StorageLocation.SOURCE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    search = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )