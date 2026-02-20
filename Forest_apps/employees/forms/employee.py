from django import forms
from Forest_apps.employees.models import Employee
from Forest_apps.core.models import Position, Warehouse


class EmployeeCreateForm(forms.ModelForm):
    """Форма создания сотрудника"""

    class Meta:
        model = Employee
        fields = ['last_name', 'first_name', 'middle_name', 'position', 'warehouse']
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию',
                'autofocus': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество (необязательно)'
            }),
            'position': forms.Select(attrs={
                'class': 'form-control'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'position': 'Должность',
            'warehouse': 'Склад',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только активными должностями и складами
        self.fields['position'].queryset = Position.get_active_positions()
        self.fields['warehouse'].queryset = Warehouse.get_active_warehouses()
        # Делаем склад необязательным
        self.fields['warehouse'].required = False

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        last_name = cleaned_data.get('last_name')
        first_name = cleaned_data.get('first_name')

        # Проверка на существующего сотрудника с таким же ФИО
        if last_name and first_name:
            middle_name = cleaned_data.get('middle_name', '')
            if Employee.objects.filter(
                    last_name__iexact=last_name,
                    first_name__iexact=first_name,
                    middle_name__iexact=middle_name,
                    is_active=True
            ).exists():
                raise forms.ValidationError('Сотрудник с таким ФИО уже существует')

        return cleaned_data


class EmployeeEditForm(forms.ModelForm):
    """Форма редактирования сотрудника"""

    class Meta:
        model = Employee
        fields = ['last_name', 'first_name', 'middle_name', 'position', 'warehouse']
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию',
                'autofocus': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество (необязательно)'
            }),
            'position': forms.Select(attrs={
                'class': 'form-control'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'position': 'Должность',
            'warehouse': 'Склад',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только активными должностями и складами
        self.fields['position'].queryset = Position.get_active_positions()
        self.fields['warehouse'].queryset = Warehouse.get_active_warehouses()
        # Делаем склад необязательным
        self.fields['warehouse'].required = False

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        last_name = cleaned_data.get('last_name')
        first_name = cleaned_data.get('first_name')
        instance = self.instance

        # Проверка на существующего сотрудника с таким же ФИО (исключая текущего)
        if last_name and first_name:
            middle_name = cleaned_data.get('middle_name', '')
            if Employee.objects.filter(
                    last_name__iexact=last_name,
                    first_name__iexact=first_name,
                    middle_name__iexact=middle_name,
                    is_active=True
            ).exclude(id=instance.id).exists():
                raise forms.ValidationError('Сотрудник с таким ФИО уже существует')

        return cleaned_data