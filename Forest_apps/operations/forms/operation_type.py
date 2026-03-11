from django import forms
from Forest_apps.operations.models import OperationType


class OperationTypeCreateForm(forms.ModelForm):
    """Форма создания типа операции"""

    class Meta:
        model = OperationType
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Распиловка, Сушка, Строгание...',
                'autofocus': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Название типа операции',
            'is_active': 'Активен',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Валидация названия - проверка на уникальность"""
        name = self.cleaned_data.get('name')
        if name:
            # Проверяем, существует ли уже такой тип операции (исключая текущий при редактировании)
            queryset = OperationType.objects.filter(name__iexact=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError('Тип операции с таким названием уже существует')
        return name


class OperationTypeFilterForm(forms.Form):
    """Форма фильтрации типов операций"""
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...'
        })
    )

    is_active = forms.ChoiceField(
        choices=[
            ('', 'Все'),
            ('true', 'Активные'),
            ('false', 'Неактивные')
        ],
        required=False,
        label='Статус',
        widget=forms.Select(attrs={
            'class': 'form-control auto-submit'
        })
    )