from django import forms
from django.utils import timezone
from Forest_apps.employees.models import WorkTimeRecord, Employee
from Forest_apps.core.models import Warehouse


class WorkTimeRecordCreateForm(forms.ModelForm):
    """Форма создания записи рабочего времени"""

    class Meta:
        model = WorkTimeRecord
        fields = ['date_time', 'warehouse', 'employee', 'hours']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'autofocus': True
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите количество часов',
                'step': '0.25',
                'min': '0'
            }),
        }
        labels = {
            'date_time': 'Дата и время',
            'warehouse': 'Склад',
            'employee': 'Сотрудник',
            'hours': 'Часы работы',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только активными складами и сотрудниками
        self.fields['warehouse'].queryset = Warehouse.get_active_warehouses()
        self.fields['employee'].queryset = Employee.get_active_employees().select_related('position')

        # Устанавливаем начальное значение даты на сегодня
        self.fields['date_time'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_hours(self):
        """Валидация количества часов"""
        hours = self.cleaned_data['hours']
        if hours <= 0:
            raise forms.ValidationError('Количество часов должно быть больше 0')
        if hours > 24:
            raise forms.ValidationError('Количество часов не может превышать 24')
        return hours

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        employee = cleaned_data.get('employee')

        # Проверка на будущие даты
        if date_time and date_time > timezone.now():
            raise forms.ValidationError('Нельзя создавать записи на будущее время')

        # Проверка на дубликаты записей для сотрудника в один день
        if date_time and employee:
            existing_record = WorkTimeRecord.objects.filter(
                employee=employee,
                date_time__date=date_time.date()
            ).exists()

            if existing_record:
                raise forms.ValidationError(
                    f'Для сотрудника {employee.short_name} уже есть запись на {date_time.date()}'
                )

        return cleaned_data


class WorkTimeRecordEditForm(forms.ModelForm):
    """Форма редактирования записи рабочего времени"""

    class Meta:
        model = WorkTimeRecord
        fields = ['date_time', 'warehouse', 'employee', 'hours']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите количество часов',
                'step': '0.25',
                'min': '0'
            }),
        }
        labels = {
            'date_time': 'Дата и время',
            'warehouse': 'Склад',
            'employee': 'Сотрудник',
            'hours': 'Часы работы',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только активными складами и сотрудниками
        self.fields['warehouse'].queryset = Warehouse.get_active_warehouses()
        self.fields['employee'].queryset = Employee.get_active_employees().select_related('position')

        # Форматируем дату для поля ввода
        if self.instance and self.instance.date_time:
            self.fields['date_time'].initial = self.instance.date_time.strftime('%Y-%m-%dT%H:%M')

    def clean_hours(self):
        """Валидация количества часов"""
        hours = self.cleaned_data['hours']
        if hours <= 0:
            raise forms.ValidationError('Количество часов должно быть больше 0')
        if hours > 24:
            raise forms.ValidationError('Количество часов не может превышать 24')
        return hours

    def clean(self):
        """Дополнительная валидация"""
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        employee = cleaned_data.get('employee')
        instance = self.instance

        # Проверка на будущие даты
        if date_time and date_time > timezone.now():
            raise forms.ValidationError('Нельзя создавать записи на будущее время')

        # Проверка на дубликаты записей для сотрудника в один день (исключая текущую)
        if date_time and employee:
            existing_record = WorkTimeRecord.objects.filter(
                employee=employee,
                date_time__date=date_time.date()
            ).exclude(id=instance.id).exists()

            if existing_record:
                raise forms.ValidationError(
                    f'Для сотрудника {employee.short_name} уже есть запись на {date_time.date()}'
                )

        return cleaned_data


class WorkTimeRecordFilterForm(forms.Form):
    """Форма для фильтрации записей рабочего времени"""

    date_from = forms.DateField(
        label='Дата с',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        label='Дата по',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    employee = forms.ModelChoiceField(
        label='Сотрудник',
        required=False,
        queryset=Employee.get_active_employees(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    warehouse = forms.ModelChoiceField(
        label='Склад',
        required=False,
        queryset=Warehouse.get_active_warehouses(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )